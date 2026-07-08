from __future__ import annotations

from app.models.state import AgentState
from app.services.risk.risk import assess_risk


def risk_node(state: AgentState) -> dict:
    score, level, factors = assess_risk(
        tool_calls=state.tool_calls,
        plan=state.plan,
    )

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_factors": factors,
    }
