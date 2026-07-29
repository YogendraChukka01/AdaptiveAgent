from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryRedis:
    """In-memory store fallback when Redis is unavailable.

    Implements only the subset of redis.asyncio.Redis methods used by
    MemoryManager.  Data is lost on process restart.
    """

    def __init__(self) -> None:
        self._data: dict[str, list[str]] = {}

    async def rpush(self, key: str, value: str) -> None:
        self._data.setdefault(key, []).append(value)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        items = self._data.get(key, [])
        return items[start:] if end == -1 else items[start:end]

    async def ltrim(self, key: str, start: int, end: int) -> None:
        items = self._data.get(key, [])
        self._data[key] = items[start:] if end == -1 else items[start:end]

    async def expire(self, key: str, ttl: int) -> None:
        pass  # Not supported — data lives until process exit.

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def aclose(self) -> None:
        self._data.clear()


class MemoryManager:
    def __init__(self):
        self._redis: redis.Redis | InMemoryRedis | None = None
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> redis.Redis | InMemoryRedis:
        if self._redis is not None:
            return self._redis
        async with self._lock:
            if self._redis is None:
                try:
                    self._redis = redis.from_url(settings.redis_url, decode_responses=True)
                except Exception:
                    logger.exception(
                        "Redis unavailable at %s; using in-memory fallback. "
                        "Conversations will not persist across restarts.",
                        settings.redis_url,
                    )
                    self._redis = InMemoryRedis()
            return self._redis

    async def get_redis(self) -> redis.Redis:
        retu