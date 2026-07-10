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


def _ragas_faithfulness(query: str, evidence: list, response: str) -> float | None:
    """Ragas-style faithfulness: extract claims, verify each against context.

    Returns faithfulness score (supported_claims / total_claims) or None
    on failure so caller falls back to heuristic scoring.
    """
    if not settings.eval_judge_model or not getattr(settings, "eval_ragas_enabled", True):
        return None
    try:
        from app.services.judge import extract_claims, verify_claims

        context_parts: list[str] = []
        for doc in evidence:
            if isinstance(doc, dict):
                context_parts.append(doc.get("content", ""))
            elif isinstance(doc, str):
                context_parts.append(doc)
        context_text = "\n".join(context_parts) if context_parts else "(no context)"

        claims = extract_claims(response)
        if not claims:
            return None

        verified = verify_claims(context_text, claims)
        if not verified:
            return None

        supported = sum(1 for v in verified if v.get("verdict", 0) == 1)
        faithfulness = supported / len(verified)
        logger.info(
            "Ragas faithfulness: %d/%d claims supported = %.3f",
            supported,
            len(verified),
            faithfulness,
        )
        return faithfulness
    except Exception:
        logger.debug("Ragas faithfulness scoring failed")
        return None


def _judge_relevancy(query: str, response: str) -> float | None:
    """LLM-as-judge answer relevancy. Returns score or None on failure."""
    if not settings.eval_judge_model or not getattr(settings, "eval_relevancy_enabled", True):
        return None
    try:
        from app.services.judge import score_relevancy

        return score_relevancy(query, response)
    except Exception:
        logger.debug("Relevancy scoring failed")
        return None


def _judge_faithfulness(query: str, evidence: list, response: str) -> float | None:
    """Simple LLM-as-judge faithfulness (single-pass). Returns score or None."""
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
        logger.debug("Judge faithfulness scoring failed")
        return None


def eval_node(state: AgentState) -> dict:
    """Evaluate response quality using heuristic + LLM-as-judge.

    Scoring pipeline:
      1. Heuristic baseline (fast, zero-cost) — length, grounding, relevance
      2. LLM judge (when eval_judge_model is set):
         a. Ragas-style faithfulness (claim extraction + NLI verification)
         b. Answer relevancy (does response address the query)
         c. Simple faithfulness (single-pass fallback if Ragas fails)
      3. Blend: weighted combination of heuristic + judge scores

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

    # LLM-as-judge scoring (when configured)
    ragas_score = _ragas_faithfulness(query, evidence, response)
    relevancy_score = _judge_relevancy(query, response)
    simple_faith_score = _judge_faithfulness(query, evidence, response)

    # Build combined score with available metrics
    judge_scores: list[tuple[float, float]] = []  # (score, weight)

    if ragas_score is not None:
        judge_scores.append((ragas_score, 0.5))
        logger.info("Ragas faithfulness: %.3f", ragas_score)
    elif simple_faith_score is not None:
        judge_scores.append((simple_faith_score, 0.4))
        logger.info("Simple faithfulness: %.3f", simple_faith_score)

    if relevancy_score is not None:
        judge_scores.append((relevancy_score, 0.3))
        logger.info("Answer relevancy: %.3f", relevancy_score)

    if judge_scores:
        total_weight = sum(w for _, w in judge_scores)
        judge_avg = sum(s * w for s, w in judge_scores) / total_weight
        combined = 0.4 * h_score + 0.6 * judge_avg
        method = "heuristic+judge"
    else:
        combined = h_score
        method = "heuristic"

    details_parts = [
        f"method={method}",
        f"length={h_details['length']:.2f}",
        f"grounding={h_details['grounding']:.2f}",
        f"relevance={h_details['relevance']:.2f}",
    ]
    if ragas_score is not None:
        details_parts.append(f"ragas={ragas_score:.3f}")
    if relevancy_score is not None:
        details_parts.append(f"relevancy={relevancy_score:.3f}")
    if simple_faith_score is not None and ragas_score is None:
        details_parts.append(f"faithfulness={simple_faith_score:.3f}")
    details_parts.append(f"combined={combined:.3f}")

    details_str = ", ".join(details_parts)

    logger.info("Eval score: %.3f (%s)", combined, details_str)

    return {
        "eval_score": round(combined, 3),
        "eval_details": details_str,
    }
