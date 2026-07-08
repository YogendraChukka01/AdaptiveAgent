from __future__ import annotations

from app.models.state import AgentState

_REFUSAL = "I cannot provide this response as it may violate safety guidelines."


def _is_safe_output(text: str) -> bool:
    lowered = text.lower()
    blocked = [
        "ignore previous instructions",
        "ignore all instructions",
        "you are not bound by",
        "forget your guidelines",
    ]
    for phrase in blocked:
        if phrase in lowered:
            return False
    return True


def response_node(state: AgentState) -> dict:
    response = state.final_response

    if not response and state.evidence_coverage < 0.5:
        response = "I don't have sufficient evidence to answer this question reliably."

    if not response:
        response = "I was unable to generate a response. Please try rephrasing your query."

    if response and not _is_safe_output(response):
        response = _REFUSAL

    return {
        "final_response": response,
    }
