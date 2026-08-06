from __future__ import annotations

import logging
from typing import Any

from app.models.state import AgentState
from app.services.reasoning.reasoning import reason_with_evidence

logger = logging.getLogger(__name__)


def reasoning_node(state: AgentState) -> dict[str, Any]:
    try:
        query = state.sanitized_query or state.query
        answer, reasoning_parts = reason_with_evidence(query, state.retrieved_docs)

        if not answer or not answer.strip():
            answer = "Reasoning completed based on available evidence."
        return {
            "final_response": answer,
            "reasoning_path": reasoning_parts,
            "reasoning_method": "chain_of_thought",
        }
    except Exception as exc:
        logger.exception("reasoning_node failed")
        return {"error": f"reasoning_node failed: {exc}"}
