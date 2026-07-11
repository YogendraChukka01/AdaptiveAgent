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
        from langchain_core.documents import Document

        docs = [
            Document(
                page_content=doc,
                metadata=(metadatas[i] if metadatas else {}) | {"_id": ids[i]},
            )
            for i, doc in enumerate(documents)
        ]
        self._get_collection().add_documents(documents=docs, ids=ids)

    def query_similar(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        collection = self._get_collection()
        results = collection.similarity_search_by_vector(
            embedding=query_embedding,
            k=n_results,
            filter=where,
        )
        return {
            "documents": [[doc.page_content for doc in results]],
            "metadatas": [[doc.metadata for doc in results]],
            "distances": [[0.0] * len(results)],
        }

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
