from __future__ import annotations

from app.models.state import ToolCallRecord

RISK_WEIGHTS: dict[str, float] = {
    "read": 5.0,
    "write": 40.0,
    "delete": 90.0,
    "financial": 60.0,
    "privacy": 50.0,
    "external_api": 30.0,
    "database": 35.0,
    "file_system": 25.0,
    "email": 20.0,
    "admin": 80.0,
}


def assess_risk(tool_calls: list[ToolCallRecord], plan: list[str]) -> tuple[float, str, dict]:
    factors: dict[str, float] = {}

    for call in tool_calls:
        tool_lower = call.tool.lower()
        for keyword, weight in RISK_WEIGHTS.items():
            if keyword in tool_lower:
                factors[f"tool:{call.tool}"] = max(
                    factors.get(f"tool:{call.tool}", 0),
                    weight,
                )

    if any("delete" in step.lower() for step in plan):
        factors["plan_has_delete"] = 90.0
    if any("write" in step.lower() for step in plan):
        factors["plan_has_write"] = 40.0
    if any("financial" in step.lower() for step in plan):
        factors["financial_query"] = 60.0
    if any("email" in step.lower() for step in plan):
        factors["email_query"] = 20.0

    if not factors:
        return 0.0, "low", {}

    tool_risks = [v for k, v in factors.items() if k.startswith("tool:")]
    other_risks = [v for k, v in factors.items() if not k.startswith("tool:")]

    if tool_risks:
        max_tool = max(tool_risks)
        avg_other = sum(other_risks) / max(len(other_risks), 1) if other_risks else 0
        total_risk = max_tool * 0.7 + avg_other * 0.3
    else:
        total_risk = sum(other_risks) / max(len(other_risks), 1)

    total_risk = min(99.0, max(0.0, total_risk))

    if total_risk >= 70.0:
        level = "high"
    elif total_risk >= 30.0:
        level = "medium"
    else:
        level = "low"

    return round(total_risk, 1), level, factors
