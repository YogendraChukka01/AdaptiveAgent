from __future__ import annotations

from app.models.state import AgentState
from app.services.evidence.evidence import verify_evidence


def evidence_node(state: AgentState) -> dict:
    query = state.sanitized_query or state.query
    result = verify_evidence(query, state.retrieved_docs)

    return {
        "evidence_coverage": result["coverage_score"],
        "evidence_contradictions": result["contradictions"],
        "evidence_missing": result["missing"],
    }
