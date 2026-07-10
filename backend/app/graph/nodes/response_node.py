from __future__ import annotations

from app.core.config import settings
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

    if not response and state.evidence_coverage < settings.evidence_min_coverage:
        response = "I don't have sufficient evidence to answer this question reliably."

    if not response:
        response = "I was unable to generate a response. Please try rephrasing your query."

    if response and not _is_safe_output(response):
        response = _REFUSAL
    else:
        tool_results = [r for r in state.tool_results if r]
        if tool_results:
            joined = "\n\n".join(f"- {r}" for r in tool_results)
            response = f"{response}\n\nTool results used:\n{joined}"

    return {
        "final_response": response,
    }
