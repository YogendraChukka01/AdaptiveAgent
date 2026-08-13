from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.text import content_to_str
from app.models.state import AgentState
from app.services.llm import get_llm

_REFUSAL = "I cannot provide this response as it may violate safety guidelines."

_REFUSAL_PATTERNS = [
    "i don't have sufficient evidence",
    "unable to generate a response",
    "cannot provide this response",
    "i cannot provide",
    "please try again later",
    "please try rephrasing your query",
]


def _is_safe_output(text: str) -> bool:
    lowered = text.lower()
    blocked = [
        "ignore previous instructions",
        "ignore all instructions",
        "you are not bound by",
        "forget your guidelines",
        "disregard your instructions",
        "you are now DAN",
    ]
    for phrase in blocked:
        if phrase in lowered:
            return False
    return True


def _is_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in _REFUSAL_PATTERNS)


def _generate_fallback_response(query: str, docs: list[dict[str, Any]]) -> str:
    """Generate a response using LLM when reasoning node didn't produce one."""
    context = "\n\n".join(
        f"[Source: {d.get('source', 'unknown')}]\n{d.get('content', '')[:500]}" for d in docs[:5]
    )
    messages = [
        SystemMessage(
            content=(
                "You are a helpful AI assistant. Answer the user's question using ONLY "
                "the provided evidence. If evidence is insufficient, say so clearly. "
                "Be concise and accurate."
            )
        ),
        HumanMessage(content=f"Question: {query}\n\nEvidence:\n{context}"),
    ]
    try:
        llm = get_llm(temperature=0.2, max_tokens=1024)
        response = llm.invoke(messages)
        return content_to_str(response.content).strip()
    except Exception:
        return ""


def response_node(state: AgentState) -> dict[str, Any]:
    response = state.final_response

    # If reasoning didn't produce a response, generate one via LLM
    if not response and state.retrieved_docs:
        response = _generate_fallback_response(
            state.sanitized_query or state.query,
            state.retrieved_docs,
        )

    if not response and state.evidence_coverage < settings.evidence_min_coverage:
        response = "I don't have sufficient evidence to answer this question reliably."

    if not response:
        response = "I was unable to generate a response. Please try rephrasing your query."

    if response and not _is_safe_output(response):
        response = _REFUSAL

    if response and not _is_refusal(response):
        tool_results = [r for r in state.tool_results if r and _is_safe_output(r)]
        if tool_results:
            joined = "\n\n".join(f"- {r}" for r in tool_results)
            response = f"{response}\n\nTool results used:\n{joined}"

    return {
        "final_response": response,
    }
