from __future__ import annotations

from pydantic import BaseModel


class ApprovalDecision(BaseModel):
    status: str
    requires_approval: bool
    reason: str


def determine_approval(risk_level: str, risk_score: float) -> ApprovalDecision:
    if risk_level == "high" or risk_score >= 70.0:
        return ApprovalDecision(
            status="pending",
            requires_approval=True,
            reason="High risk action requires human approval",
        )
    elif risk_level == "medium" or risk_score >= 30.0:
        return ApprovalDecision(
            status="approved",
            requires_approval=False,
            reason="Medium risk - auto-approved (optional approval configured)",
        )
    else:
        return ApprovalDecision(
            status="approved",
            requires_approval=False,
            reason="Low risk - automatic execution",
        )
