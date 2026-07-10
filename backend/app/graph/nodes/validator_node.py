from __future__ import annotations

from app.models.state import AgentState
from app.services.validator.validator import validate_query


def query_validator(state: AgentState) -> dict:
    query = state.messages[-1].content if state.messages else state.query

    result = validate_query(query)

    if not result.is_safe:
        safety_msg = (
            "I cannot process this request as it was identified as unsafe. "
            f"Issues detected: {', '.join(result.issues)}"
        )
        return {
            "is_safe": False,
            "safety_issues": result.issues,
            "safety_confidence": result.confidence,
            "error": safety_msg,
            "final_response": safety_msg,
        }

    return {
        "is_safe": True,
        "sanitized_query": query,
        "safety_issues": [],
        "safety_confidence": result.confidence,
    }
