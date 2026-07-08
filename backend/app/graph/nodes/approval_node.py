from __future__ import annotations

from app.models.state import AgentState
from app.services.approval.approval import determine_approval


def approval_node(state: AgentState) -> dict:
    decision = determine_approval(
        risk_level=state.risk_level,
        risk_score=state.risk_score,
    )

    return {
        "approval_status": decision.status,
    }
