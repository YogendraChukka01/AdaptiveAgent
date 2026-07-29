from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.services.memory.memory import memory_manager

logger = logging.getLogger(__name__)

_PENDING_KEY = "safeagent:pending_approvals"


async def _redis():
    try:
        return await memory_manager.get_redis()
    except Exception as e:  # Redis unavailable - degrade, never block approvals.
        logger.warning("pending-approval tracking unavailable: %s", e)
        return None


async def track_pending_approval(
    thread_id: str,
    risk_level: str | None,
    risk_score: float | None,
    query: str = "",
) -> None:
    """Record that a thread is waiting on human approval (with a timestamp)."""
    if not settings.approval_ttl_seconds:
        return
    r = await _redis()
    if r is None:
        return
    payload = {
        "thread_id": thread_id,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "query": query[:500],
        "created_at": time.time(),
    }
    try:
        await r.hset(_PENDING_KEY, thread_id, json.dumps(payload))
    except Exception as e:
        logger.warning("track_pending_approval failed: %s", e)


async def clear_pending_approval(thread_id: str) -> None:
    r = await _redis()
    if r is None:
        return
    try:
        await r.hdel(_PENDING_KEY, thread_id)
    except Exception as e:
        logger.warning("clear_pending_approval failed: %s", e)


async def list_pending_approvals(
    include_expired: bool = True,
) -> list[dict[str, Any]]:
    """List threads awaiting approval.

    With include_expired=False, only threads still within the configured TTL
    are returned (callers can treat the rest as orphaned and expire them).
    """
    r = await _redis()
    if r is None:
        return []
    try:
        raw = await r.hgetall(_PENDING_KEY)
    except Exception as e:
        logger.warning("list_pending_approvals failed: %s", e)
        return []
    out: list[dict[str, Any]] = []
    now = time.time()
    for value in raw.values():
        try:
            entry = json.loads(value)
        except json.JSONDecodeError:
            continue
        age = now - entry.get("created_at", now)
        entry["age_seconds"] = age
        entry["expired"] = (
            bool(settings.approval_ttl_seconds) and age > settings.approval_ttl_seconds
        )
        if include_expired or not entry["expired"]:
            out.append(entry)
    out.sort(key=lambda e: e.get("created_at", 0.0))
    return out


async def expire_pending_approvals() -> int:
    """Reject every approval thread that exceeded the TTL. Returns count expired."""
    pending = await list_pending_approvals(include_expired=True)
    expired = [e for e in pending if e.get("expired")]
    for e in expired:
        await clear_pending_approval(e["thread_id"])
    return len(expired)
