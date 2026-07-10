from __future__ import annotations

import logging

from app.services.retrieval.vector_store.base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class QdrantVectorStore(BaseVectorStore):
    """Qdrant vector store backend.

    Requires: pip install qdrant-client langchain-qdrant
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        super().__init__(config)
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient

                self._client = QdrantClient(
                    url=self.config.qdrant_url,
                    prefer_grpc=self.config.qdrant_grpc,
                )
            except ImportError:
                raise ImportError(
                    "QdrantVectorStore requires qdrant-client. "
                    "Install with: pip install qdrant-client langchain-qdrant"
                )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            try:
                from langchain_core.embeddings import Embeddings
                from langchain_qdrant import QdrantVectorStore

                client = self._get_client()

                class _PassthroughEmbedder(Embeddings):
                    def embed_documents(self, texts):
                        return [[] for _ in texts]

                    def embed_query(self, text):
                        return []

                self._collection = QdrantVectorStore(
                    client=client,
                    collection_name=self.config.collection_name,
                    embedding=_PassthroughEmbedder(),
                )
            except ImportError:
                raise ImportError(
                    "QdrantVectorStore requires langchain-qdrant. "
                    "Install with: pip install langchain-qdrant"
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
                metadata=metadatas[i] if metadatas else {},
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
        results = self._get_collection().similarity_search_by_vector(
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
        self._get_client().delete(
            collection_name=self.config.collection_name,
            points_selector=ids,
        )

    def count(self) -> int:
        collection_info = self._get_client().get_collection(self.config.collection_name)
        return collection_info.points_count or 0

    def get_or_create_collection(self, name: str | None = None) -> object:
        return self._get_collection()
