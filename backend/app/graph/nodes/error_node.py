from __future__ import annotations

from app.models.state import AgentState


def error_node(state: AgentState) -> dict:
    error_msg = state.error or "An unexpected error occurred during processing."
    return {
        "final_response": f"I encountered an error while processing your request: {error_msg}",
        "error": error_msg,
    }
