from __future__ import annotations

from app.models.state import AgentState
from app.services.confidence.confidence import calculate_confidence


def confidence_node(state: AgentState) -> dict:
    score, factors = calculate_confidence(
        retrieval_scores=state.retrieval_scores,
        evidence_coverage=state.evidence_coverage,
        num_supporting_docs=len(state.retrieved_docs),
    )

    return {
        "confidence_score": score,
        "confidence_factors": factors,
    }
