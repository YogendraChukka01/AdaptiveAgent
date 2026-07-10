from __future__ import annotations

import json
import logging

from app.models.state import AgentState, ToolCallRecord
from app.services.tools.tool_registry import execute_tool

logger = logging.getLogger(__name__)


def tools_node(state: AgentState) -> dict:
    if not state.tool_calls:
        return {}

    if state.approval_status not in ("approved", "not_required"):
        return {"error": "Tool execution blocked: approval not granted"}

    executed: list[ToolCallRecord] = []
    for record in state.tool_calls:
        if record.success:
            executed.append(
                ToolCallRecord(
                    tool=record.tool,
                    input=record.input,
                    output=record.output,
                    success=True,
                    duration_ms=record.duration_ms,
                )
            )
            continue

        try:
            args = json.loads(record.input) if isinstance(record.input, str) else record.input
        except (json.JSONDecodeError, TypeError):
            args = {}

        result = execute_tool(record.tool, args)
        executed.append(result)

    return {
        "tool_calls": executed,
        "tool_results": [r.output or "" for r in executed],
    }
