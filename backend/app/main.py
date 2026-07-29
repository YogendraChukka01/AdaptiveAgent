from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import audit, chat, evaluate, health, upload
from app.api.health import close_health_client
from app.core.config import settings
from app.core.database import init_db
from app.core.deps import init_graph, shutdown_graph
from app.core.threads import expire_pending_approvals
from app.services.memory.memory import memory_manager
from app.services.memory.memory_worker import memory_distiller

logger = logging.getLogger(__name__)


def _configure_tracing() -> None:
    """Enable LangSmith tracing when an API key is configured.

    Gated entirely on settings.langsmith_api_key so local/dev runs are
    unaffected. Env must be set before LangChain is first used.
    Only sets each variable if another component hasn't already set it.
    """
    if not settings.langsmith_api_key:
        return
    if "LANGCHAIN_TRACING_V2" not in os.environ:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if "LANGCHAIN_API_KEY" not in os.environ:
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    if "LANGCHAIN_PROJECT" not in os.environ:
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project


async def _expire_pending_approvals_loop():
    """Periodically reject approval threads that exceeded the TTL."""
    while True:
        try:
            expired = await expire_pending_approvals()
            if expired:
                logger.info("Expired %d pending approval(s)", expired)
        except Exception:
            logger.exception("Failed to expire pending approvals")
        await asyncio.sleep(settings.approval_ttl_seconds // 2 or 300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_tracing()
    await init_db()
    await init_graph()
    await memory_distiller.start()

    expire_task = asyncio.create_task(_expire_pending_approvals_loop())

    yield

    expire_task.cancel()
    try:
        await expire_task
    except asyncio.CancelledError:
        pass
    await memory_distiller.stop()
    await memory_manager.close()
    await close_health_client()
    await shutdown_graph()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(audit.router)
app.include_router(evaluate.router)
