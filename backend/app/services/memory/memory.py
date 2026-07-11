from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


class MemoryManager:
    def __init__(self):
        self._redis: redis.Redis | None = None
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> redis.Redis:
        async with self._lock:
            if self._redis is None:
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            else:
                try:
                    await self._redis.ping()
                except (redis.ConnectionError, redis.TimeoutError, OSError):
                    self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            return self._redis

    async def get_redis(self) -> redis.Redis:
        return await self._get_redis()

    async def close(self):
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def store_conversation(
        self,
        thread_id: str,
        role: str,
        content: str,
        trust_score: float = 1.0,
        ttl: int = 86400,
    ):
        r = await self._get_redis()
        entry = {
            "role": role,
            "content": content,
            "trust_score": trust_score,
            "timestamp": time.time(),
        }
        key = f"conversation:{thread_id}"
        await r.rpush(key, json.dumps(entry))
        await r.ltrim(key, -200, -1)
        await r.expire(key, ttl)

    async def get_conversation(self, thread_id: str, limit: int = 50) -> list[dict[str, Any]]:
        r = await self._get_redis()
        key = f"conversation:{thread_id}"
        entries = await r.lrange(key, -limit, -1)
        result = []
        for entry in entries:
            try:
                result.append(json.loads(entry))
            except json.JSONDecodeError:
                continue
        return result

    async def clear_conversation(self, thread_id: str):
        r = await self._get_redis()
        await r.delete(f"conversation:{thread_id}")


memory_manager = MemoryManager()
