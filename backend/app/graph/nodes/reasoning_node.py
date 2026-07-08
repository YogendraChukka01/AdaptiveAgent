from __future__ import annotations

from app.models.state import AgentState
from app.services.reasoning.reasoning import reason_with_evidence


def reasoning_node(state: AgentState) -> dict:
    query = state.sanitized_query or state.query
    answer, reasoning_parts = reason_with_evidence(query, state.retrieved_docs)

    return {
        "final_response": answer,
        "reasoning_path": reasoning_parts,
        "reasoning_method": "chain_of_thought",
    }
