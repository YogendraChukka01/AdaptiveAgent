from __future__ import annotations

from app.models.state import AgentState
from app.services.planner.planner import create_plan


def planner_node(state: AgentState) -> dict:
    query = state.sanitized_query or state.query

    if not query.strip():
        return {"plan": [], "current_plan_step": 0}

    plan = create_plan(query)
    return {"plan": plan, "current_plan_step": 0}
