from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.services.llm import get_llm

logger = logging.getLogger(__name__)

_JUDGE_SYSTEM = SystemMessage(
    content=(
        "You are a faithfulness judge for a RAG system. Given a USER QUERY, "
        "RETRIEVED CONTEXT, and an AI RESPONSE, score how faithful the response "
        "is to the provided context.\n\n"
        "Rules:\n"
        "- A faithful response uses ONLY information found in the context.\n"
        "- Hallucinated facts, unsupported claims, or information not in the "
        "context reduces the score.\n"
        "- Partial faithfulness gets a proportional score.\n\n"
        "Return EXACTLY one line in this format:\n"
        "SCORE: <float between 0.0 and 1.0>\n"
        "No other text."
    )
)

_CLAIM_SYSTEM = SystemMessage(
    content=(
        "You are a claim extractor for a RAG faithfulness judge. Given an AI "
        "RESPONSE, extract every factual claim as a JSON array of short strings.\n\n"
        'Return ONLY a JSON array, e.g. ["claim 1", "claim 2"]. '
        "No other text."
    )
)

_NLI_SYSTEM = SystemMessage(
    content=(
        "You are a natural language inference judge. For each CLAIM, determine "
        "if it is SUPPORTED or NOT SUPPORTED by the CONTEXT.\n\n"
        "Return a JSON array of objects with 'claim' and 'verdict' (1 for "
        "SUPPORTED, 0 for NOT SUPPORTED).\n"
        'Example: [{"claim": "...", "verdict": 1}, {"claim": "...", "verdict": 0}]\n'
        "No other text."
    )
)

_RELEVANCY_SYSTEM = SystemMessage(
    content=(
        "You are an answer relevancy judge. Given a USER QUERY and an AI "
        "RESPONSE, score how well the response addresses the query.\n\n"
        "Return EXACTLY one line in this format:\n"
        "SCORE: <float between 0.0 and 1.0>\n"
        "No other text."
    )
)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def _parse_json_array(text: str) -> list:
    """Extract a JSON array from LLM output, handling markdown fences."""
    text = text.strip().strip("`").strip()
    if text.startswith("json\n"):
        text = text[5:]
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []


def _parse_score(text: str) -> float | None:
    """Extract a SCORE: <float> from LLM output."""
    match = re.search(r"SCORE:\s*([\d.]+)", text)
    if match:
        return max(0.0, min(1.0, float(match.group(1))))
    try:
        return max(0.0, min(1.0, float(text.strip())))
    except ValueError:
        return None


def score_faithfulness(query: str, context: str, response: str) -> float:
    """LLM-as-judge faithfulness score in [0, 1].

    Uses the configured LLM with temperature=0 and a short prompt for
    speed.  Returns 0.0 on any failure so the heuristic fallback in
    eval_node remains the default scoring path.
    """
    try:
        llm = get_llm(temperature=0.0, max_tokens=32)
        max_ctx = getattr(settings, "eval_judge_max_chars", 1500)

        user_msg = HumanMessage(
            content=(
                f"USER QUERY: {_truncate(query, 300)}\n\n"
                f"RETRIEVED CONTEXT:\n{_truncate(context, max_ctx)}\n\n"
                f"AI RESPONSE:\n{_truncate(response, 1000)}\n\n"
                "Score faithfulness (0.0 = fully hallucinated, "
                "1.0 = perfectly grounded in context):"
            )
        )

        resp = llm.invoke([_JUDGE_SYSTEM, user_msg])  # type: ignore[union-attr]
        text = resp.content.strip()  # type: ignore[union-attr]

        score = _parse_score(text)
        return score if score is not None else 0.0
    except Exception:
        logger.debug("LLM judge failed, returning 0.0 fallback")
        return 0.0


def extract_claims(response: str) -> list[str]:
    """Extract factual claims from a response using LLM.

    Ragas-style: decompose response into individual claims before
    verification. Returns empty list on failure.
    """
    if not settings.eval_judge_model:
        return []
    try:
        llm = get_llm(temperature=0.0, max_tokens=256)
        user_msg = HumanMessage(
            content=(
                f"AI RESPONSE:\n{_truncate(response, 2000)}\n\n"
                "Extract every factual claim as a JSON array of short strings."
            )
        )
        resp = llm.invoke([_CLAIM_SYSTEM, user_msg])  # type: ignore[union-attr]
        return _parse_json_array(resp.content)  # type: ignore[union-attr]
    except Exception:
        logger.debug("Claim extraction failed")
        return []


def verify_claims(context: str, claims: list[str]) -> list[dict]:
    """Verify claims against context using NLI.

    Returns list of {"claim": str, "verdict": 0|1} dicts.
    """
    if not claims or not settings.eval_judge_model:
        return [{"claim": c, "verdict": 1} for c in claims]
    try:
        llm = get_llm(temperature=0.0, max_tokens=512)
        max_ctx = getattr(settings, "eval_judge_max_chars", 1500)

        claims_text = json.dumps(claims[:15])  # limit to 15 claims
        user_msg = HumanMessage(
            content=(
                f"CONTEXT:\n{_truncate(context, max_ctx)}\n\n"
                f"CLAIMS:\n{claims_text}\n\n"
                "For each claim, return verdict 1 (SUPPORTED) or 0 (NOT SUPPORTED)."
            )
        )
        resp = llm.invoke([_NLI_SYSTEM, user_msg])  # type: ignore[union-attr]
        results = _parse_json_array(resp.content)  # type: ignore[union-attr]
        verified = []
        for item in results:
            if isinstance(item, dict) and "claim" in item and "verdict" in item:
                verified.append(
                    {
                        "claim": str(item["claim"]),
                        "verdict": 1 if item["verdict"] else 0,
                    }
                )
        return verified if verified else [{"claim": c, "verdict": 1} for c in claims]
    except Exception:
        logger.debug("Claim verification failed, assuming all supported")
        return [{"claim": c, "verdict": 1} for c in claims]


def score_relevancy(query: str, response: str) -> float:
    """LLM-as-judge answer relevancy score in [0, 1].

    Measures how well the response addresses the user's query.
    Returns None on failure so caller can skip this metric.
    """
    if not settings.eval_judge_model:
        return 0.0
    try:
        llm = get_llm(temperature=0.0, max_tokens=32)
        user_msg = HumanMessage(
            content=(
                f"USER QUERY: {_truncate(query, 300)}\n\n"
                f"AI RESPONSE:\n{_truncate(response, 1000)}\n\n"
                "Score answer relevancy (0.0 = completely off-topic, "
                "1.0 = perfectly addresses the query):"
            )
        )
        resp = llm.invoke([_RELEVANCY_SYSTEM, user_msg])  # type: ignore[union-attr]
        text = resp.content.strip()  # type: ignore[union-attr]
        score = _parse_score(text)
        return score if score is not None else 0.0
    except Exception:
        logger.debug("Relevancy judge failed")
        return 0.0
