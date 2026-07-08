from __future__ import annotations

import re

from pydantic import BaseModel, Field
from sunglasses.engine import SunglassesEngine

from app.core.config import settings


class ValidationResult(BaseModel):
    is_safe: bool
    issues: list[str] = Field(default_factory=list)
    confidence: float = 0.0


_engine: SunglassesEngine | None = None


def _get_engine() -> SunglassesEngine:
    global _engine
    if _engine is None:
        _engine = SunglassesEngine()
    return _engine


PII_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{16}\b"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
]

SQL_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|TRUNCATE)\b", re.IGNORECASE),
    re.compile(r"(--|;|'/ *|1=1)"),
]


def validate_query(query: str) -> ValidationResult:
    issues: list[str] = []

    if not query.strip():
        issues.append("empty_query")

    if len(query) > settings.max_query_length:
        issues.append("query_too_long")
        return ValidationResult(is_safe=False, issues=issues, confidence=0.0)

    ss = _get_engine()
    result = ss.scan(query)
    if not result.is_clean:
        issues.append(f"prompt_injection_detected (severity: {result.severity})")

    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(query):
            issues.append("sql_injection_detected")
            break

    for pattern in PII_PATTERNS:
        if pattern.search(query):
            issues.append("pii_detected")
            break

    is_safe = len(issues) == 0

    severity_map = {"critical": 0.95, "high": 0.75, "medium": 0.50, "low": 0.25}
    confidence = 1.0 - severity_map.get(result.severity, 0.0) if not result.is_clean else 1.0
    return ValidationResult(
        is_safe=is_safe,
        issues=issues,
        confidence=confidence,
    )
