from __future__ import annotations

import logging

from app.services.retrieval.vector_store.base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class PGVectorStore(BaseVectorStore):
    """PGVector vector store backend.

    Requires: pip install langchain-postgres psycopg2-binary
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        super().__init__(config)
        self._engine = None
        self._collection = None
        self._collection_id = None

    def _get_engine(self):
        if self._engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine

            self._engine = create_async_engine(self.config.pg_connection_string)
        return self._engine

    def _get_collection(self):
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

    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        import asyncio
        import json

        import asyncpg

        async def _insert():
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
                        self._get_or_create_collection_id(conn),
                        embeddings[i],
                        documents[i],
                        json.dumps(meta),
                        ids[i],
                    )
            finally:
                await conn.close()

        try:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(_insert())
        except RuntimeError:
            asyncio.run(_insert())

    def query_similar(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        import asyncio
        import json

        import asyncpg

        async def _query():
            conn = await asyncpg.connect(self.config.pg_connection_string.replace("+asyncpg", ""))
            try:
                collection_id = self._get_or_create_collection_id(conn)
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
                documents = []
                metadatas = []
                distances = []
                for row in rows:
                    documents.append(row["document"] or "")
                    metadatas.append(json.loads(row["cmetadata"]) if row["cmetadata"] else {})
                    distances.append(float(row["distance"]))
                return documents, metadatas, distances
            finally:
                await conn.close()

        try:
            loop = asyncio.get_running_loop()
            documents, metadatas, distances = loop.run_until_complete(_query())
        except RuntimeError:
            documents, metadatas, distances = asyncio.run(_query())

        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    def _get_or_create_collection_id(self, conn) -> str:
        import asyncio
        import uuid

        async def _get_or_create():
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

        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(_get_or_create())
        except RuntimeError:
            return asyncio.run(_get_or_create())

    def delete(self, ids: list[str]) -> None:
        self._get_collection().delete(ids=ids)

    def count(self) -> int:
        collection = self._get_collection()
        try:
            return collection.count()
        except Exception:
            logger.warning("PGVector count() failed, returning 0")
            return 0

    def get_or_create_collection(self, name: str | None = None) -> object:
        return self._get_collection()
