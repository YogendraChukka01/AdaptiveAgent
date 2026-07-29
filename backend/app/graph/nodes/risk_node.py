from __future__ import annotations

import logging

from app.models.state import AgentState
from app.services.risk.risk import assess_risk

logger = logging.getLogger(__name__)


def risk_node(state: AgentState) -> dict:
    try:
        score, level, factors = assess_risk(
            tool_calls=state.tool_calls,
            plan=state.plan,
        )

        return {
            "risk_score": score,
            "risk_level": level,
            "risk_factors": factors,
        }
    except Exception as exc:
        logger.exception("risk_node failed")
        return {"error": f"risk_node failed: {exc}"}
