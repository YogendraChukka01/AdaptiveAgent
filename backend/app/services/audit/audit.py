from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, text

from app.core.database import Base, async_session_factory

logger = logging.getLogger(__name__)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(255), index=True, nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="low")
    confidence_score = Column(Float, default=0.0)
    approval_status = Column(String(20), default="not_required")
    tool_calls = Column(Text, nullable=True)
    citations = Column(Text, nullable=True)
    execution_time_ms = Column(Float, default=0.0)
    step_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


async def record_audit(entry: dict[str, Any]) -> None:
    try:
        async with async_session_factory() as session:
            log = AuditLog(
                thread_id=entry.get("thread_id", ""),
                query=entry.get("query", ""),
                response=entry.get("response", ""),
                risk_score=entry.get("risk_score", 0.0),
                risk_level=entry.get("risk_level", "low"),
                confidence_score=entry.get("confidence_score", 0.0),
                approval_status=entry.get("approval_status", "not_required"),
                tool_calls=json.dumps(entry.get("tool_calls", [])),
                citations=json.dumps(entry.get("citations", [])),
                execution_time_ms=entry.get("execution_time_ms", 0.0),
                step_count=entry.get("step_count", 0),
                error=entry.get("error"),
            )
            session.add(log)
            await session.commit()
    except Exception:
        logger.warning(
            "Failed to record audit log for thread %s",
            entry.get("thread_id"),
            exc_info=True,
        )
