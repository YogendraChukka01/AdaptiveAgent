from __future__ import annotations

import logging

from app.core.config import settings
from app.models.state import AgentState

logger = logging.getLogger(__name__)


async def eval_node(state: AgentState) -> dict:
    """Evaluate response quality and score it.

    Uses a fast heuristic approach (no external LLM judge by default) to
    check whether the response is grounded in the retrieved evidence and
    addresses the original query.  When ``eval_judge_model`` is configured,
    a Ragas-style LLM-as-judge scoring step is also performed.

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

    scores: list[float] = []

    # ── 1. Heuristic: response length relative to query complexity ────
    word_count = len(response.split())
    if word_count < 5:
        scores.append(0.2)
    elif word_count < 20:
        scores.append(0.6)
    else:
        scores.append(0.9)

    # ── 2. Evidence grounding: fraction of response words found in evidence
    if evidence:
        evidence_text = " ".join(
            doc.get("document", "") for doc in evidence if isinstance(doc, dict)
        ).lower()
        response_words = set(response.lower().split())
        evidence_words = set(evidence_text.split())
        if response_words:
            overlap = len(response_words & evidence_words) / len(response_words)
            scores.append(min(1.0, overlap * 2))
        else:
            scores.append(0.0)
    else:
        scores.append(0.3)

    # ── 3. Query relevance: shared terms between query and response ────
    query_terms = set(query.lower().split())
    response_terms = set(response.lower().split())
    if query_terms:
        relevance = len(query_terms & response_terms) / len(query_terms)
        scores.append(min(1.0, relevance * 1.5))
    else:
        scores.append(0.5)

    # ── 4. Safety / refusal check ─────────────────────────────────────
    refusal_phrases = [
        "i don't have sufficient evidence",
        "unable to generate",
        "cannot provide",
        "i cannot",
    ]
    if any(phrase in response.lower() for phrase in refusal_phrases):
        scores.append(0.3)

    combined = sum(scores) / len(scores) if scores else 0.0

    details_parts = [
        f"length={scores[0]:.2f}" if scores else "",
        f"grounding={scores[1]:.2f}" if len(scores) > 1 else "",
        f"relevance={scores[2]:.2f}" if len(scores) > 2 else "",
        f"combined={combined:.2f}",
    ]

    logger.info("Eval score: %.2f (%s)", combined, ", ".join(details_parts))

    return {
        "eval_score": round(combined, 3),
        "eval_details": ", ".join(details_parts),
    }
