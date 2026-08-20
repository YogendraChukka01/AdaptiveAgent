from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create tables if they don't exist (development only).

    In production, schema changes should be applied via Alembic migrations:
        alembic upgrade head

    This function uses create_all() as a convenience for local development
    and is safe to call on startup — it is a no-op when tables already exist.
    For production, set up Alembic:
        pip install alembic
        alembic init alembic
        alembic revision --autogenerate -m "initial"
        alembic upgrade head
    """
    env = settings.environment.lower()
    if env in ("production", "prod"):
        logger.warning(
            "⚠️  init_db() called in production. "
            "Schema management should be done via Alembic migrations "
            "(alembic upgrade head). Skipping create_all() in production."
        )
        return

    async with engine.begin() as conn:
        # Import models here so SQLAlchemy knows about them before create_all
        from app.models import audit  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified (dev mode)")


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
