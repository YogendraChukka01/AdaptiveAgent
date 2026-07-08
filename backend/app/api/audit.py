from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.database import async_session_factory
from app.services.audit.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    thread_id: str | None = None,
):
    async with async_session_factory() as session:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())

        if thread_id:
            query = query.where(AuditLog.thread_id == thread_id)

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": log.id,
                "thread_id": log.thread_id,
                "query": log.query[:200],
                "risk_score": log.risk_score,
                "risk_level": log.risk_level,
                "confidence_score": log.confidence_score,
                "approval_status": log.approval_status,
                "execution_time_ms": log.execution_time_ms,
                "step_count": log.step_count,
                "error": log.error,
                "created_at": str(log.created_at),
            }
            for log in logs
        ]
