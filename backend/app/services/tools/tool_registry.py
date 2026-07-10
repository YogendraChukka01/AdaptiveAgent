from __future__ import annotations

import os
import time
from typing import Any

from langchain_core.tools import tool

from app.models.state import ToolCallRecord


class ToolResult:
    def __init__(self, success: bool, output: str, error: str | None = None):
        self.success = success
        self.output = output
        self.error = error


_TOOL_TIMEOUT = 30.0
_MAX_RETRIES = 2
_MAX_FILE_READ = 1024 * 1024  # 1 MB


@tool
def web_search(query: str) -> str:
    """Search the web for information. Input: a search query string."""
    return f"[Simulated] Web search results for: {query}"


_ALLOWED_READ_DIRS: list[str] = [os.getcwd()]

AVAILABLE_TOOLS: set[str] = {"web_search", "read_file"}


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
        with open(resolved, "r") as f:
            return f.read(_MAX_FILE_READ)
    except Exception as e:
        return f"Error reading file: {e}"


def execute_tool(name: str, args: dict[str, Any]) -> ToolCallRecord:
    start = time.time()
    last_error: str | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            tools_map = {
                "web_search": web_search,
                "read_file": read_file,
            }
            if name not in tools_map:
                return ToolCallRecord(
                    tool=name,
                    input=str(args),
                    success=False,
                    error=f"Unknown tool: {name}",
                    duration_ms=0.0,
                )

            fn = tools_map[name]
            result = fn.invoke(args)

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
            time.sleep(0.5 * (attempt + 1))

    duration = (time.time() - start) * 1000
    return ToolCallRecord(
        tool=name,
        input=str(args),
        output=None,
        success=False,
        error=last_error,
        duration_ms=round(duration, 2),
    )
