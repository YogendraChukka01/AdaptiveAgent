from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from app.models.state import AgentState
from app.services.llm import get_llm

logger = logging.getLogger(__name__)


def _refine_query(query: str, attempt: int, evidence_missing: list[str]) -> str:
    """Produce a better retrieval query for the next attempt.

    Implements the CRAG / Self-RAG "repair" step: when retrieval or
    confidence is weak, blindly repeating the same query cannot help, so we
    rewrite it to be more specific / decomposed, or broaden it. An LLM is used
    when available; otherwise a deterministic fallback guarantees the query
    still changes so re-retrieval is not identical.
    """
    try:
        llm = get_llm(temperature=0.3, max_tokens=256)
        prompt = (
            "The previous search for the query below returned insufficient or "
            "low-coverage evidence. Rewrite it to be more specific and retrievable, "
            "or split it into sub-questions. Return only the rewritten query.\n"
            f"Original: {query}"
        )
        out = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        if out:
            return out
    except Exception:
        logger.debug("LLM refine failed, using deterministic fallback")

    # Deterministic fallback: bias the query toward what was missing, else
    # broaden it with generic context terms.
    if evidence_missing:
        return f"{query} {' '.join(evidence_missing[:3])}"
    suffixes = ("overview", "context", "background")
    return f"{query} {suffixes[attempt % len(suffixes)]}"


def refine_node(state: AgentState) -> dict:
    retry_count = state.retry_count + 1
    base = state.sanitized_query or state.query
    refined = _refine_query(base, retry_count, state.evidence_missing)

    return {
        "retry_count": retry_count,
        "sanitized_query": refined,
        "refined_query": refined,
        # keep counting toward the circuit breaker on every retry iteration
        "step_count": state.step_count + 1,
    }
