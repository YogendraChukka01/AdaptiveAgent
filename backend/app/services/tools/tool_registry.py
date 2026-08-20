from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from langchain_core.tools import tool

from app.core.config import settings
from app.models.state import ToolCallRecord

logger = logging.getLogger(__name__)


class ToolResult:
    def __init__(self, success: bool, output: str, error: str | None = None):
        self.success = success
        self.output = output
        self.error = error


_TOOL_TIMEOUT = 30.0
_MAX_RETRIES = 2
_MAX_FILE_READ = 1024 * 1024  # 1 MB

AVAILABLE_TOOLS: set[str] = {"web_search", "read_file"}


# ── Web Search ────────────────────────────────────────────────────────────────

def _tavily_search(query: str, max_results: int) -> str:
    """Search using Tavily API."""
    try:
        from tavily import TavilyClient  # type: ignore[import]
        client = TavilyClient(api_key=settings.web_search_api_key)
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])
        if not results:
            return "No results found."
        lines = []
        for r in results:
            lines.append(f"Title: {r.get('title', '')}")
            lines.append(f"URL: {r.get('url', '')}")
            lines.append(f"Content: {r.get('content', '')[:500]}")
            lines.append("---")
        return "\n".join(lines)
    except ImportError:
        return "Error: tavily-python package not installed. Run: pip install tavily-python"
    except Exception as e:
        return f"Tavily search error: {e}"


def _serpapi_search(query: str, max_results: int) -> str:
    """Search using SerpAPI."""
    try:
        import httpx
        params = {
            "q": query,
            "api_key": settings.web_search_api_key,
            "num": max_results,
            "engine": "google",
        }
        resp = httpx.get("https://serpapi.com/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        organic = data.get("organic_results", [])
        if not organic:
            return "No results found."
        lines = []
        for r in organic[:max_results]:
            lines.append(f"Title: {r.get('title', '')}")
            lines.append(f"URL: {r.get('link', '')}")
            lines.append(f"Snippet: {r.get('snippet', '')}")
            lines.append("---")
        return "\n".join(lines)
    except Exception as e:
        return f"SerpAPI search error: {e}"


def _brave_search(query: str, max_results: int) -> str:
    """Search using Brave Search API."""
    try:
        import httpx
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": settings.web_search_api_key or "",
        }
        params = {"q": query, "count": max_results}
        resp = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("web", {}).get("results", [])
        if not results:
            return "No results found."
        lines = []
        for r in results[:max_results]:
            lines.append(f"Title: {r.get('title', '')}")
            lines.append(f"URL: {r.get('url', '')}")
            lines.append(f"Description: {r.get('description', '')}")
            lines.append("---")
        return "\n".join(lines)
    except Exception as e:
        return f"Brave search error: {e}"


def _perform_web_search(query: str) -> str:
    """Route to the configured search provider."""
    provider = (settings.web_search_provider or "none").lower()
    max_results = settings.web_search_max_results

    if provider == "none" or not provider:
        return (
            "[web_search unavailable] No search provider configured. "
            "Set WEB_SEARCH_PROVIDER and WEB_SEARCH_API_KEY in your .env to enable real search. "
            f"Query was: {query}"
        )

    if not settings.web_search_api_key:
        return (
            f"[web_search error] WEB_SEARCH_PROVIDER={provider} but WEB_SEARCH_API_KEY is not set."
        )

    if provider == "tavily":
        return _tavily_search(query, max_results)
    if provider == "serpapi":
        return _serpapi_search(query, max_results)
    if provider == "brave":
        return _brave_search(query, max_results)

    return f"[web_search error] Unknown provider: {provider}. Supported: tavily, serpapi, brave"


@tool
def web_search(query: str) -> str:
    """Search the web for information. Input: a search query string.

    Returns real search results when WEB_SEARCH_PROVIDER is configured,
    or a clear unavailability message when no provider is set.
    """
    if not query or not query.strip():
        return "Error: empty search query"
    return _perform_web_search(query.strip())


# ── File Read ─────────────────────────────────────────────────────────────────

_ALLOWED_READ_DIRS: list[str] = [os.getcwd()]


def configure_read_dirs(dirs: list[str]) -> None:
    _ALLOWED_READ_DIRS.clear()
    _ALLOWED_READ_DIRS.extend(dirs)


@tool
def read_file(filepath: str) -> str:
    """Read a file. Input: absolute file path (must be within allowed directories)."""
    resolved = os.path.realpath(os.path.normpath(filepath))
    if _ALLOWED_READ_DIRS:
        allowed = False
        for d in _ALLOWED_READ_DIRS:
            allowed_dir = os.path.realpath(os.path.normpath(d))
            if resolved == allowed_dir or resolved.startswith(allowed_dir + os.sep):
                allowed = True
                break
        if not allowed:
            return "Error: access denied — file not in allowed directory"
    try:
        with open(resolved) as f:
            return f.read(_MAX_FILE_READ)
    except Exception as e:
        return f"Error reading file: {e}"


# ── Executor ──────────────────────────────────────────────────────────────────

_TOOLS_MAP = {
    "web_search": web_search,
    "read_file": read_file,
}


async def execute_tool(name: str, args: dict[str, Any]) -> ToolCallRecord:
    start = time.time()
    last_error: str | None = None

    if name not in _TOOLS_MAP:
        return ToolCallRecord(
            tool=name,
            input=str(args),
            success=False,
            error=f"Unknown tool: {name}",
            duration_ms=0.0,
        )

    fn = _TOOLS_MAP[name]

    for attempt in range(_MAX_RETRIES):
        try:
            result = await asyncio.to_thread(fn.invoke, args)
            duration = (time.time() - start) * 1000
            return ToolCallRecord(
                tool=name,
                input=str(args),
                output=str(result),
                success=True,
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            last_error = str(e)
            logger.warning("Tool %s attempt %d failed: %s", name, attempt + 1, e)
            await asyncio.sleep(0.5 * (attempt + 1))

    duration = (time.time() - start) * 1000
    return ToolCallRecord(
        tool=name,
        input=str(args),
        output=None,
        success=False,
        error=last_error,
        duration_ms=round(duration, 2),
    )
