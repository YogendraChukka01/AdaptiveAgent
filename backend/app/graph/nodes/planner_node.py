from __future__ import annotations

import logging
from typing import Any

from app.models.state import AgentState
from app.services.planner.planner import create_plan

logger = logging.getLogger(__name__)


def planner_node(state: AgentState) -> dict[str, Any]:
    if state.retry_count >= state.max_retries:
        return {"error": "Max planner retries exceeded"}
    try:
        query = state.sanitized_query or state.query

        if not query.strip():
            return {"plan": []}

        plan = create_plan(query)
        return {"plan": plan}
    except Exception as exc:
        logger.exception("planner_node failed")
        return {"error": f"planner_node failed: {exc}"}
