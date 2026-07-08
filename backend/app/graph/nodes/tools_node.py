from __future__ import annotations

import json

from app.models.state import AgentState
from app.services.tools.tool_registry import execute_tool


def tools_node(state: AgentState) -> dict:
    if not state.tool_calls:
        return {}

    if state.approval_status not in ("approved", "not_required"):
        return {"error": "Tool execution blocked: approval not granted"}

    executed = []
    for record in state.tool_calls:
        try:
            args = json.loads(record.input) if isinstance(record.input, str) else record.input
        except json.JSONDecodeError:
            args = {"input": record.input}

        result = execute_tool(record.tool, args)
        executed.append(result)

    return {"tool_calls": executed}
