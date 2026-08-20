from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── SunglassesEngine (optional semantic prompt-injection detector) ─────────────
_sunglasses_available: bool = False
_SunglassesEngine: Any = None

try:
    from sunglasses import SunglassesEngine as _SE  # type: ignore[import]
    _SunglassesEngine = _SE
    _sunglasses_available = True
    logger.info("SunglassesEngine loaded successfully — semantic injection detection active.")
except ImportError:
    logger.warning(
        "⚠️  SunglassesEngine not installed (pip install sunglasses). "
        "Falling back to regex-only prompt-injection detection. "
        "Install sunglasses for stronger semantic safety coverage."
    )

# ── Compiled regex patterns ────────────────────────────────────────────────────
_SQL_INJECTION = re.compile(
    r"\b(UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO|DELETE\s+FROM"
    r"|EXEC\s*\(|xp_cmdshell|;\s*DROP|--\s*$)",
    re.IGNORECASE,
)
_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                   # SSN
    re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),  # Credit cards
    re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),  # Email
    re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),           # Phone
]
_INJECTION_PHRASES = [
    "ignore previous instructions",
    "disregard your instructions",
    "forget your instructions",
    "you are now",
    "new instructions:",
    "system override",
    "pretend you are",
    "act as if you have no restrictions",
    "reveal your system prompt",
    "ignore all previous",
    "forget everything above",
    "skip all restrictions",
    "bypass your filters",
]
_INJECTION_RE = re.compile(
    "|".join(re.escape(p) for p in _INJECTION_PHRASES),
    re.IGNORECASE,
)

# Singleton
_engine_instance: Any = None
_engine_init_attempted: bool = False


def _get_engine() -> Any:
    global _engine_instance, _engine_init_attempted
    if _engine_init_attempted:
        return _engine_instance
    _engine_init_attempted = True
    if not _sunglasses_available:
        return None
    try:
        _engine_instance = _SunglassesEngine()
    except Exception:
        logger.exception("SunglassesEngine init failed — regex-only fallback.")
        _engine_instance = None
    return _engine_instance


def _regex_injection_check(query: str) -> bool:
    """Return True if the query looks like a prompt injection attempt."""
    return bool(_INJECTION_RE.search(query))


def validate_query(query: str) -> dict[str, Any]:
    """Validate a user query for injection, SQL attacks, and PII.

    Returns:
        {"valid": bool, "reason": str | None, "has_pii": bool}
    """
    if not query or not query.strip():
        return {"valid": False, "reason": "Empty query", "has_pii": False}

    # SQL injection check
    if _SQL_INJECTION.search(query):
        return {
            "valid": False,
            "reason": "Query contains SQL injection patterns",
            "has_pii": False,
        }

    # PII detection
    has_pii = any(p.search(query) for p in _PII_PATTERNS)

    # Prompt injection — try semantic engine first, fall back to regex
    engine = _get_engine()
    if engine is not None:
        try:
            result = engine.detect(query)
            is_injection = getattr(result, "is_injection", False)
            if is_injection:
                return {
                    "valid": False,
                    "reason": "Potential prompt injection detected (semantic)",
                    "has_pii": has_pii,
                }
        except Exception:
            logger.debug("SunglassesEngine detection failed; using regex fallback")
            if _regex_injection_check(query):
                return {
                    "valid": False,
                    "reason": "Potential prompt injection detected (regex fallback)",
                    "has_pii": has_pii,
                }
    else:
        if _regex_injection_check(query):
            return {
                "valid": False,
                "reason": "Potential prompt injection detected",
                "has_pii": has_pii,
            }

    return {"valid": True, "reason": None, "has_pii": has_pii}
