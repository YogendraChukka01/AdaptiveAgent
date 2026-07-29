from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.state import AgentState, ToolCallRecord
from app.services.tools.tool_registry import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a tool-selection agent for a safe RAG assistant.
Given the user query and the plan, decide which external tools (if any) are required.
Available tools:
- web_search: search the web for up-to-date information. args: {"query": "..."}
- read_file: read a local file. args: {"filepath": "..."}

Return a JSON array of objects, e.g. [{"tool": "web_search", "args": {"query": "..."}}].
Only include tools that are clearly needed. If none are needed, return [].
Do not invent tools that are not in the available list."""


def plan_tool_calls(query: str, plan: list[str]) -> list[ToolCallRecord]:
    try:
        from app.services.llm import get_llm

        llm = get_llm(temperature=0.0, max_tokens=512)
        plan_str = ", ".join(plan) if plan else "(no plan)"
        response = llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Query: {query}\nPlan: {plan_str}"),
            ]
        )

        try:
            parsed = json.loads(response.content.strip())
        except (json.JSONDecodeError, ValueError):
            return []

        if not isinstance(parsed, list):
            return []

        calls: list[ToolCallRecord] = []
        for item in parsed[:5]:
            if not isinstance(item, dict):
                continue
            name = item.get("tool")
            if name not in AVAILABLE_TOOLS:
                continue
            args = item.get("args", {})
            if not isinstance(args, dict):
                args = {}
            calls.append(
                ToolCallRecord(
                    tool=name,
                    input=json.dumps(args),
                    success=False,
                )
            )
        return calls
    except Exception:
        logger.exception("Tool planning failed")
        return []


def tool_planner_node(state: AgentState) -> dict:
    query = state.sanitized_query or state.query
    if not query.strip():
        return {"tool_calls": []}
    return {"tool_calls": plan_tool_calls(query, state.plan)}
