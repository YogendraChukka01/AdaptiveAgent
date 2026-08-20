from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.models.state import AgentState

logger = logging.getLogger(__name__)

# ── Judge module ───────────────────────────────────────────────────────────────
# Imported at module level so that import errors are loud at startup rather than
# silently swallowed at runtime (I-13).
_judge_available: bool = False
_score_faithfulness = None
_score_relevancy = None

try:
    from app.services.judge import score_faithfulness as _sf
    from app.services.judge import score_relevancy as _sr

    _score_faithfulness = _sf
    _score_relevancy = _sr
    _judge_available = True
    logger.info("Judge module loaded — LLM-as-judge evaluation active.")
except Exception as exc:
    logger.warning(
        "Judge module unavailable (%s). "
        "Evaluation will use heuristic scoring only. "
        "Ensure app.services.judge is importable and its dependencies are installed.",
        exc,
    )


# ── Heuristic scoring ─────────────────────────────────────────────────────────

def _heuristic_score(state: AgentState) -> tuple[float, str]:
    """Produce a [0, 1] quality score from easily available signals.

    Components:
    - length_score:     penalises extremely short or empty responses
    - grounding_score:  fraction of retrieved docs cited in the response
    - relevance_score:  rough keyword overlap between query and response

    Returns (score, detail_string).
    """
    response = state.final_response or ""
    query = state.sanitized_query or state.query or ""
    docs = state.retrieved_docs or []

    # Length score: 0 for empty, 1 for ≥150 chars, linear in between
    length_score = min(1.0, len(response) / 150) if response else 0.0

    # Grounding: fraction of doc sources mentioned in the response
    if docs:
        mentioned = sum(
            1
            for d in docs
            if d.get("source", "") and d["source"].lower() in response.lower()
        )
        grounding_score = min(1.0, mentioned / max(len(docs), 1))
    else:
        # No docs expected (e.g. pure reasoning task) → neutral
        grounding_score = 0.6

    # Relevance: Jaccard-style word overlap query ↔ response
    query_words = set(query.lower().split())
    response_words = set(response.lower().split())
    if query_words:
        overlap = len(query_words & response_words)
        relevance_score = min(1.0, overlap / max(len(query_words), 1))
    else:
        relevance_score = 0.5

    score = (length_score * 0.3 + grounding_score * 0.35 + relevance_score * 0.35)
    detail = (
        f"heuristic: length={length_score:.2f}, "
        f"grounding={grounding_score:.2f}, "
        f"relevance={relevance_score:.2f}"
    )
    return round(score, 3), detail


def eval_node(state: AgentState) -> dict[str, Any]:
    """Evaluate the response quality and decide whether to refine.

    Scoring strategy (in order of preference):
    1. LLM-as-judge (faithfulness + relevancy) when judge module and
       eval_judge_model are both available.
    2. Heuristic scoring otherwise.

    The eval_threshold in config is calibrated for the active mode:
    - 0.70 (default) works for heuristic-only scoring.
    - Raise to 0.85 in config when eval_judge_model is configured.
    """
    if not settings.eval_enabled:
        return {"eval_score": 1.0, "eval_details": "evaluation disabled"}

    if not state.final_response:
        return {
            "eval_score": 0.0,
            "eval_details": "no response to evaluate",
            "should_refine": True,
        }

    score: float
    detail: str

    if _judge_available and settings.eval_judge_model:
        query = state.sanitized_query or state.query or ""
        response = state.final_response
        context = "\n\n".join(d.get("content", "") for d in (state.retrieved_docs or []))

        faithfulness = _score_faithfulness(query, context, response)  # type: ignore[misc]

        relevancy: float | None = None
        if settings.eval_relevancy_enabled:
            try:
                relevancy = _score_relevancy(query, response)  # type: ignore[misc]
            except Exception:
                logger.debug("Relevancy scoring failed; skipping")

        if relevancy is not None:
            score = faithfulness * 0.6 + relevancy * 0.4
            detail = f"judge: faithfulness={faithfulness:.2f}, relevancy={relevancy:.2f}"
        else:
            score = faithfulness
            detail = f"judge: faithfulness={faithfulness:.2f}"
    else:
        score, detail = _heuristic_score(state)

    should_refine = score < settings.eval_threshold

    if should_refine:
        logger.info(
            "Response quality below threshold (%.2f < %.2f) — triggering refine. %s",
            score,
            settings.eval_threshold,
            detail,
        )

    return {
        "eval_score": score,
        "eval_details": detail,
        "should_refine": should_refine,
    }
