from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.deps import init_graph
from app.services.memory.memory_worker import memory_distiller

logger = logging.getLogger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    _production_startup_checks()

    logger.info("Initialising graph…")
    await init_graph()
    logger.info("Graph ready")

    await memory_distiller.start()

    if settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    yield

    # Shutdown
    await memory_distiller.stop()
    logger.info("Shutdown complete")


def _production_startup_checks() -> None:
    """Log warnings / hard-fail on insecure production config."""
    env = settings.environment.lower()
    is_prod = env in ("production", "prod")

    if not settings.api_key:
        if is_prod:
            raise RuntimeError(
                "FATAL: API_KEY must be set before starting in production. "
                "Generate one with: openssl rand -hex 32"
            )
        logger.warning(
            "⚠️  API_KEY is not set — authentication is DISABLED. "
            "Set API_KEY in .env before deploying to production."
        )

    if not settings.auth_jwt_secret or "dev" in settings.auth_jwt_secret.lower():
        if is_prod:
            raise RuntimeError(
                "FATAL: AUTH_JWT_SECRET must be a strong random value in production."
            )
        logger.warning("⚠️  AUTH_JWT_SECRET looks weak or is using the dev default.")

    _log_search_provider_status()


def _log_search_provider_status() -> None:
    provider = (settings.web_search_provider or "none").lower()
    if provider == "none" or not provider:
        logger.warning(
            "ℹ️  web_search tool is configured with provider='none'. "
            "The tool will return a clear unavailability message instead of real results. "
            "Set WEB_SEARCH_PROVIDER and WEB_SEARCH_API_KEY in .env to enable real search."
        )
    elif not settings.web_search_api_key:
        logger.warning(
            "⚠️  WEB_SEARCH_PROVIDER=%s but WEB_SEARCH_API_KEY is not set — "
            "search calls will fail at runtime.",
            provider,
        )
    else:
        logger.info("✅ web_search provider: %s", provider)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# ── Prometheus metrics (Fix I-16) ─────────────────────────────────────────────
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ── Rate limiting middleware (Fix I-09) ───────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.chat import router as chat_router
from app.api.upload import router as upload_router

app.include_router(chat_router, prefix="/api")
app.include_router(upload_router, prefix="/api")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health() -> dict[str, Any]:
    checks: dict[str, str] = {}

    try:
        import httpx

        r = await httpx.AsyncClient().get(
            f"{settings.ollama_base_url}/api/tags", timeout=3.0
        )
        checks["ollama"] = "ok" if r.status_code == 200 else f"http_{r.status_code}"
    except Exception as e:
        checks["ollama"] = f"error: {e}"

    try:
        import chromadb

        client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
        client.heartbeat()
        checks["chroma"] = "ok"
    except Exception as e:
        checks["chroma"] = f"error: {e}"

    try:
        from app.core.database import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    # Web search provider status
    provider = (settings.web_search_provider or "none").lower()
    has_key = bool(settings.web_search_api_key)
    if provider == "none":
        checks["web_search"] = "disabled (no provider configured)"
    elif not has_key:
        checks["web_search"] = f"misconfigured: provider={provider} but no API key"
    else:
        checks["web_search"] = f"ok (provider={provider})"

    # SunglassesEngine status
    try:
        from app.services.validator.validator import _sunglasses_available  # type: ignore[attr-defined]
        checks["sunglasses_engine"] = "ok" if _sunglasses_available else "unavailable (regex-only fallback)"
    except ImportError:
        checks["sunglasses_engine"] = "unknown"

    overall = "healthy" if all(v == "ok" or v.startswith("ok") or "disabled" in v for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "version": "1.0.0"}
