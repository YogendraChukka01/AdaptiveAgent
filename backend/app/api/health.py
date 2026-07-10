from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.models.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    ollama_ok = False
    chroma_ok = False
    db_ok = False

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception as e:
        logger.warning("Ollama health check failed: %s", e)

    try:
        from app.services.retrieval.vector_store.chroma_store import get_chroma_client

        get_chroma_client().heartbeat()
        chroma_ok = True
    except Exception as e:
        logger.warning("ChromaDB health check failed: %s", e)

    try:
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.warning("Database health check failed: %s", e)

    return HealthResponse(
        status="ok",
        ollama_connected=ollama_ok,
        chroma_connected=chroma_ok,
        db_connected=db_ok,
    )
