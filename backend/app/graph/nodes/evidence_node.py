from __future__ import annotations

import logging

from app.models.state import AgentState
from app.services.evidence.evidence import verify_evidence

logger = logging.getLogger(__name__)


def evidence_node(state: AgentState) -> dict:
    try:
        query = state.sanitized_query or state.query
        result = verify_evidence(query, state.retrieved_docs)

        return {
            "evidence_coverage": result["coverage_score"],
            "evidence_contradictions": result["contradictions"],
            "evidence_missing": result["missing"],
        }
    except Exception as exc:
        logger.exception("evidence_node failed")
        return {"error": f"evidence_node failed: {exc}"}
