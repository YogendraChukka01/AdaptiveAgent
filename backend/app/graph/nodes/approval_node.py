from __future__ import annotations

from langgraph.types import interrupt

from app.models.state import AgentState
from app.services.approval.approval import determine_approval


def approval_node(state: AgentState) -> dict:
    decision = determine_approval(
        risk_level=state.risk_level,
        risk_score=state.risk_score,
        tool_calls=state.tool_calls,
        plan=state.plan,
    )

    if decision.status != "pending":
        return {"approval_status": decision.status}

    # Pause for human-in-the-loop approval. The value returned by
    # `interrupt()` is whatever the client passes to Command(resume=...).
    human_input = interrupt(
        {
            "type": "approval_required",
            "risk_level": state.risk_level,
            "risk_score": state.risk_score,
            "reason": decision.reason,
            "requires_approval": True,
            "pending_tools": decision.pending_tools,
            "triggering_factors": decision.triggering_factors,
        }
    )

    approved = (
        bool(human_input.get("approved"))
        if isinstance(human_input, dict)
        else bool(human_input)
    )

    return {"approval_status": "approved" if approved else "rejected"}
