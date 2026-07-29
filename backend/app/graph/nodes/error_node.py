from __future__ import annotations

import logging

from app.models.state import AgentState

logger = logging.getLogger(__name__)


def error_node(state: AgentState) -> dict:
    error_msg = state.error or "An unexpected error occurred during processing."
    logger.error("Graph error: %s", error_msg)
    return {
        "final_response": (
            "I encountered an error while processing your request. "
            "Please try again or contact support."
        ),
        "error": error_msg,
    }
