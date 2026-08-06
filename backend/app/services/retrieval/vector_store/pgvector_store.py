from __future__ import annotations

import logging
from typing import Any

from app.services.retrieval.vector_store.base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class PGVectorStore(BaseVectorStore):
    """PGVector vector store backend.

    Requires: pip install langchain-postgres psycopg2-binary

    NOTE: the base ``BaseVectorStore`` interface is synchronous, but this
    backend's ``add_documents``/``query_similar`` are async (asyncpg is
    inherently async). Nothing in the app currently routes through this
    backend, so the divergence is suppressed rather than realigned. Align
    this backend with the sync base contract (or drop it) before enabling.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        super().__init__(config)
        self._engine: Any = None
        self._collection: Any = None

    def _get_engine(self) -> Any:
        if self._engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine

            self._engine = create_async_engine(self.config.pg_connection_string)
        return self._engine

    def _get_collection(self) -> Any:
        if self._collection is None:
            try:
                from langchain_postgres import PGVector

                self._collection = PGVector(
                    connection=self._get_engine(),
                    collection_name=self.config.collection_name,
                )
            except ImportError:
                raise ImportError(
                    "PGVector requires langchain-postgres. "
                    "Install with: pip install langchain-postgres psycopg2-binary"
                )
        return self._collection

    async def add_documents(  # type: ignore[override]  # async vs sync base contract
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        import json

        import asyncpg

        conn = await asyncpg.connect(self.config.pg_connection_string.replace("+asyncpg", ""))
        try:
            for i in range(len(ids)):
                meta = (metadatas[i] if metadatas else {}) | {"_id": ids[i]}
                await conn.execute(
                    """
                    INSERT INTO langchain_pg_embedding
                        (collection_id, embedding, document, cmetadata, custom_id)
                    VALUES ($1, $2, $3, $4::jsonb, $5)
                    ON CONFLICT (collection_id, custom_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        document = EXCLUDED.document,
                        cmetadata = EXCLUDED.cmetadata
                    """,
                    await self._get_or_create_collection_id(conn),
                    embeddings[i],
                    documents[i],
                    json.dumps(meta),
                    ids[i],
                )
        finally:
            await conn.close()

    async def query_similar(  # type: ignore[override]  # async vs sync base contract
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import json

        import asyncpg

        conn = await asyncpg.connect(self.config.pg_connection_string.replace("+asyncpg", ""))
        try:
            collection_id = await self._get_or_create_collection_id(conn)
            rows = await conn.fetch(
                """
                SELECT document, cmetadata, embedding <=> $1 AS distance
                FROM langchain_pg_embedding
                WHERE collection_id = $2
                ORDER BY embedding <=> $1
                LIMIT $3
                """,
                query_embedding,
                collection_id,
                n_results,
            )
            documents: list[str] = []
            metadatas: list[dict[str, Any]] = []
            distances: list[float] = []
            for row in rows:
                documents.append(row["document"] or "")
                metadatas.append(json.loads(row["cmetadata"]) if row["cmetadata"] else {})
                distances.append(float(row["distance"]))
        finally:
            await conn.close()

        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    async def _get_or_create_collection_id(self, conn: Any) -> str:
        import uuid

        row = await conn.fetchrow(
            "SELECT uuid FROM langchain_pg_collection WHERE name = $1",
            self.config.collection_name,
        )
        if row:
            return str(row["uuid"])
        coll_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO langchain_pg_collection (uuid, name) VALUES ($1, $2)",
            coll_id,
            self.config.collection_name,
        )
        return coll_id

    def delete(self, ids: list[str]) -> None:
        self._get_collection().delete(ids=ids)

    def count(self) -> int:
        collection = self._get_collection()
        try:
            return int(collection.count())
        except Exception:
            logger.warning("PGVector count() failed, returning 0")
            return 0

    def get_or_create_collection(self, name: str | None = None) -> Any:
        return self._get_collection()
