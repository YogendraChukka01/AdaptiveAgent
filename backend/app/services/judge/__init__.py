from __future__ import annotations

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


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


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

        match = re.search(r"SCORE:\s*([\d.]+)", text)
        if match:
            return max(0.0, min(1.0, float(match.group(1))))

        return max(0.0, min(1.0, float(text)))
    except Exception:
        logger.debug("LLM judge failed, returning 0.0 fallback")
        return 0.0
