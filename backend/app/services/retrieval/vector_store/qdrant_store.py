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
        from qdrant_client.models import PointStruct

        client = self._get_client()
        points = [
            PointStruct(
                id=ids[i],
                vector=embeddings[i],
                payload={
                    "page_content": documents[i],
                    "metadata": (metadatas[i] if metadatas else {}),
                },
            )
            for i in range(len(ids))
        ]
        client.upsert(
            collection_name=self.config.collection_name,
            points=points,
        )

    def query_similar(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        client = self._get_client()
        results = client.search(
            collection_name=self.config.collection_name,
            query_vector=query_embedding,
            limit=n_results,
        )
        documents = []
        metadatas = []
        distances = []
        for hit in results:
            payload = hit.payload or {}
            documents.append(payload.get("page_content", ""))
            metadatas.append(payload.get("metadata", {}))
            distances.append(hit.score or 0.0)
        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
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
