from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.state import CompiledStateGraph
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings
from app.graph.builder import build_graph


def _build_serde():
    """Build the checkpoint serializer, registering pydantic state types.

    Without this, LangGraph warns (and future versions will refuse) when
    checkpointing pydantic models such as ToolCallRecord.
    """
    try:
        from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

        return JsonPlusSerializer(allowed_msgpack_modules=[("app.models.state", "ToolCallRecord")])
    except Exception:
        return None


_graph: CompiledStateGraph | None = None
_pool: AsyncConnectionPool | None = None
_init_lock = asyncio.Lock()


async def init_graph() -> CompiledStateGraph:
    global _pool, _graph
    async with _init_lock:
        if _graph is not None:
            return _graph
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url.replace("+asyncpg", ""),
            min_size=2,
            max_size=10,
            open=True,
            timeout=30,
        )
        serde = _build_serde()
        checkpointer = AsyncPostgresSaver(pool=_pool, serde=serde)
        await checkpointer.setup()
        _graph = build_graph(checkpointer=checkpointer)
        return _graph


async def get_graph() -> AsyncGenerator[CompiledStateGraph, None]:
    yield await init_graph()


async def shutdown_graph() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
