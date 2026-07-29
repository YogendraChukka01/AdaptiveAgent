from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.services.llm import get_llm

logger = logging.getLogger(__name__)

_LLM_SEMAPHORE = asyncio.Semaphore(5)


class MemoryDistiller:
    """Background worker that periodically distills conversation threads into
    concise user-fact summaries stored in ChromaDB for cross-session retrieval.

    Each fact is stored with the user/thread ID so that a future session can
    retrieve relevant context even when a different ``thread_id`` is used.
    """

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._collection = None
        self._chroma_client = None
        self._running = False
        self._chroma_unavailable = False

    async def _ensure_chroma(self) -> None:
        """Lazily initialise the ChromaDB client and collection."""
        if self._collection is not None or self._chroma_unavailable:
            return

        def _init():
            import chromadb

            self._chroma_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
            )
            self._collection = self._chroma_client.get_or_create_collection(
                name="user_facts",
                metadata={"hnsw:space": "cosine"},
            )

        try:
            await asyncio.to_thread(_init)
        except Exception:
            logger.warning("ChromaDB unavailable; memory distillation disabled")
            self._chroma_unavailable = True

    async def start(self) -> None:
        """Start the background distillation loop."""
        if not settings.memory_distill_enabled:
            return
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "Memory distiller started (interval=%dm)",
            settings.memory_distill_interval_minutes,
        )

    async def _loop(self) -> None:
        interval = settings.memory_distill_interval_minutes * 60
        while self._running:
            await asyncio.sleep(interval)
            try:
                await self._distill()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Memory distillation error")

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._collection = None
        self._chroma_client = None

    async def _distill(self) -> None:
        """Extract facts from recent conversations and store them."""
        await self._ensure_chroma()
        if not self._collection:
            return

        from app.services.memory.memory import memory_manager

        r = await memory_manager.get_redis()
        keys = []
        async for key in r.scan_iter(match="conversation:*", count=100):
            keys.append(key)
            if len(keys) >= 50:
                break
        if not keys:
            return

        total_facts = 0
        for key in keys:
            thread_id = key.split(":", 1)[1] if ":" in key else key
            entries = await r.lrange(key, -settings.memory_distill_max_messages, -1)
            if len(entries) < 4:
                continue

            messages = []
            for entry in entries:
                try:
                    obj = json.loads(entry)
                    role = obj.get("role", "user")
                    content = obj.get("content", "")
                    if content:
                        messages.append(f"{role}: {content}")
                except json.JSONDecodeError:
                    continue

            if not messages:
                continue

            facts = await self._extract_facts(messages)
            if facts:
                await self._store_facts(thread_id, facts)
                total_facts += len(facts)

        if total_facts:
            logger.info("Distilled %d facts from %d threads", total_facts, len(keys))

    async def _extract_facts(self, messages: list[str]) -> list[str]:
        """Use LLM to extract factual statements about the user."""
        async with _LLM_SEMAPHORE:
            try:
                from langchain_core.messages import HumanMessage

                def _call_llm():
                    llm = get_llm(temperature=0.0, max_tokens=512)
                    conversation = "\n".join(messages[-20:])
                    prompt = (
                        "Extract key facts and durable preferences about this user "
                        "from the conversation. Return ONLY a JSON array of short "
                        "strings (one fact each). Include only facts that would be "
                        "useful in future conversations. Do not include transient "
                        "requests or opinions.\n\n"
                        f"Conversation:\n{conversation}\n\n"
                        'Return JSON array of fact strings, e.g. ["fact 1", "fact 2"]'
                    )
                    return llm.invoke([HumanMessage(content=prompt)])  # type: ignore[union-attr]

                response = await asyncio.wait_for(asyncio.to_thread(_call_llm), timeout=120)
                content = response.content.strip()  # type: ignore[union-attr]
                content = content.strip("`").strip()
                if content.startswith("json\n"):
                    content = content[5:]
                import re

                match = re.search(r"\[.*\]", content, re.DOTALL)
                if match:
                    return json.loads(match.group())
                return json.loads(content)
            except Exception:
                logger.debug("Fact extraction failed")
                return []

    async def _store_facts(self, thread_id: str, facts: list[str]) -> None:
        """Store facts in ChromaDB for cross-session retrieval."""
        if not self._collection:
            return
        now = datetime.now(timezone.utc).isoformat()

        def _delete_and_upsert():
            self._collection.delete(where={"thread_id": thread_id})
            for i, fact in enumerate(facts):
                self._collection.upsert(
                    documents=[fact],
                    ids=[f"{thread_id}_fact_{i}"],
                    metadatas=[
                        {
                            "thread_id": thread_id,
                            "extracted_at": now,
                            "source": "distillation",
                        }
                    ],
                )

        await asyncio.to_thread(_delete_and_upsert)

    async def retrieve_facts(self, thread_id: str, query: str, k: int = 5) -> list[str]:
        """Retrieve relevant user facts for a new session."""
        await self._ensure_chroma()
        if not self._collection:
            return []
        try:
            results = await asyncio.to_thread(
                self._collection.query,
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"],
            )
            docs = results.get("documents", [[]])
            return docs[0] if docs else []
        except Exception:
            return []


memory_distiller = MemoryDistiller()
