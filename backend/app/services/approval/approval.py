from __future__ import annotations

from pydantic import BaseModel

from app.models.state import ToolCallRecord

# Tool categories that always demand human review regardless of model score.
SENSITIVE_TOOLS: frozenset[str] = frozenset({
    "delete", "admin", "write", "financial", "email", "database",
})


class ApprovalDecision(BaseModel):
    status: str
    requires_approval: bool
    reason: str
    # Names of the tool calls that triggered the review (for the UI/audit).
    pending_tools: list[str] = []
    # Risk factors (e.g. "tool:admin_console", "plan_has_delete") that triggered it.
    triggering_factors: list[str] = []


def _sensitive_tools(tool_calls: list[ToolCallRecord]) -> list[str]:
    names: list[str] = []
    for call in tool_calls:
        lowered = call.tool.lower()
        if any(seg in lowered for seg in SENSITIVE_TOOLS):
            names.append(call.tool)
    return names


def determine_approval(
    risk_level: str,
    risk_score: float,
    tool_calls: list[ToolCallRecord] | None = None,
    plan: list[str] | None = None,
) -> ApprovalDecision:
    tool_calls = tool_calls or []
    plan = plan or []

    pending = _sensitive_tools(tool_calls)
    triggering: list[str] = [f"tool:{t}" for t in pending]

    plan_has_delete = any("delete" in step.lower() for step in plan)
    plan_has_financial = any("financial" in step.lower() for step in plan)
    if plan_has_delete:
        triggering.append("plan_has_delete")
    if plan_has_financial:
        triggering.append("plan_has_financial")

    needs_approval = bool(pending) or plan_has_delete or plan_has_financial

    if risk_level == "high" or risk_score >= 70.0 or needs_approval:
        return ApprovalDecision(
            status="pending",
            requires_approval=True,
            reason=(
                "High-risk action requires human approval"
                + (f" (sensitive tools: {', '.join(pending)})" if pending else "")
            ),
            pending_tools=pending,
            triggering_factors=triggering,
        )

    if risk_level == "medium" or risk_score >= 30.0:
        return ApprovalDecision(
            status="approved",
            requires_approval=False,
            reason="Medium risk - auto-approved (optional approval configured)",
        )

    return ApprovalDecision(
        status="approved",
        requires_approval=False,
        reason="Low risk - automatic execution",
    )
