from __future__ import annotations

import logging
from typing import Any

from app.models.state import AgentState
from app.services.confidence.confidence import calculate_confidence

logger = logging.getLogger(__name__)


def confidence_node(state: AgentState) -> dict[str, Any]:
    try:
        score, factors = calculate_confidence(
            retrieval_scores=state.retrieval_scores,
            evidence_coverage=state.evidence_coverage,
            num_supporting_docs=len(state.retrieved_docs),
        )

        return {
            "confidence_score": score,
            "confidence_factors": factors,
        }
    except Exception as exc:
        logger.exception("confidence_node failed")
        return {"error": f"confidence_node failed: {exc}"}
