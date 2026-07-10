from __future__ import annotations

import logging

from app.core.config import settings
from app.models.state import AgentState

logger = logging.getLogger(__name__)


def _heuristic_score(response: str, query: str, evidence: list) -> tuple[float, dict]:
    """Fast deterministic scoring without LLM calls."""
    scores: list[float] = []

    # 1. Response length
    word_count = len(response.split())
    if word_count < 5:
        scores.append(0.2)
    elif word_count < 20:
        scores.append(0.6)
    else:
        scores.append(0.9)

    # 2. Evidence grounding
    if evidence:
        evidence_parts: list[str] = []
        for doc in evidence:
            if isinstance(doc, dict):
                evidence_parts.append(doc.get("content", ""))
            elif isinstance(doc, str):
                evidence_parts.append(doc)
        evidence_text = " ".join(evidence_parts).lower()
        response_words = set(response.lower().split())
        evidence_words = set(evidence_text.split())
        if response_words:
            overlap = len(response_words & evidence_words) / len(response_words)
            scores.append(min(1.0, overlap * 2))
        else:
            scores.append(0.0)
    else:
        scores.append(0.3)

    # 3. Query relevance
    query_terms = set(query.lower().split())
    response_terms = set(response.lower().split())
    if query_terms:
        relevance = len(query_terms & response_terms) / len(query_terms)
        scores.append(min(1.0, relevance * 1.5))
    else:
        scores.append(0.5)

    # 4. Refusal penalty (applied as multiplier, not averaged element)
    refusal_phrases = [
        "i don't have sufficient evidence",
        "unable to generate",
        "cannot provide",
        "i cannot",
    ]
    is_refusal = any(phrase in response.lower() for phrase in refusal_phrases)

    combined = sum(scores) / len(scores) if scores else 0.0
    if is_refusal:
        combined *= 0.5
    details = {
        "length": scores[0] if scores else 0.0,
        "grounding": scores[1] if len(scores) > 1 else 0.0,
        "relevance": scores[2] if len(scores) > 2 else 0.0,
    }
    return combined, details


def _llm_judge_score(query: str, evidence: list, response: str) -> float | None:
    """Call the LLM-as-judge for faithfulness scoring.  Returns None on failure."""
    if not settings.eval_judge_model:
        return None
    try:
        from app.services.judge import score_faithfulness

        context_parts: list[str] = []
        for doc in evidence:
            if isinstance(doc, dict):
                context_parts.append(doc.get("content", ""))
            elif isinstance(doc, str):
                context_parts.append(doc)
        context_text = "\n".join(context_parts) if context_parts else "(no context)"
        return score_faithfulness(query, context_text, response)
    except Exception:
        logger.debug("LLM judge unavailable, falling back to heuristic")
        return None


def eval_node(state: AgentState) -> dict:
    """Evaluate response quality using heuristic + optional LLM-as-judge.

    Scoring pipeline:
      1. Heuristic baseline (fast, zero-cost) — length, grounding, relevance
      2. LLM judge (when eval_judge_model is set) — faithfulness to context
      3. Blend: 60% heuristic + 40% LLM judge when both available

    Returns:
        eval_score (0–1): combined quality score
        eval_details: human-readable explanation
    """
    if not settings.eval_enabled:
        return {"eval_score": 1.0, "eval_details": "evaluation disabled"}

    response = state.final_response
    query = state.sanitized_query or state.query
    evidence = state.retrieved_docs

    if not response:
        return {"eval_score": 0.0, "eval_details": "empty response"}

    h_score, h_details = _heuristic_score(response, query, evidence)

    llm_score = _llm_judge_score(query, evidence, response)

    if llm_score is not None:
        combined = 0.6 * h_score + 0.4 * llm_score
        method = "heuristic+judge"
    else:
        combined = h_score
        method = "heuristic"

    details_str = (
        f"method={method}, "
        f"length={h_details['length']:.2f}, "
        f"grounding={h_details['grounding']:.2f}, "
        f"relevance={h_details['relevance']:.2f}"
        + (f", judge={llm_score:.2f}" if llm_score is not None else "")
        + f", combined={combined:.2f}"
    )

    logger.info("Eval score: %.2f (%s)", combined, details_str)

    return {
        "eval_score": round(combined, 3),
        "eval_details": details_str,
    }
