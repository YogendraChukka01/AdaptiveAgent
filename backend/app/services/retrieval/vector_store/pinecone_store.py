from __future__ import annotations

import logging

from app.services.retrieval.vector_store.base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class PineconeVectorStore(BaseVectorStore):
    """Pinecone vector store backend.

    Requires: pip install pinecone-client langchain-pinecone
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        super().__init__(config)
        self._index = None
        self._collection = None

    def _get_index(self):
        if self._index is None:
            try:
                from pinecone import Pinecone

                pc = Pinecone(api_key=self.config.pinecone_api_key)
                self._index = pc.Index(self.config.pinecone_index_name)
            except ImportError:
                raise ImportError(
                    "PineconeVectorStore requires pinecone-client. "
                    "Install with: pip install pinecone-client langchain-pinecone"
                )
        return self._index

    def _get_collection(self):
        if self._collection is None:
            try:
                from langchain_core.embeddings import Embeddings
                from langchain_pinecone import PineconeVectorStore

                class _PassthroughEmbedder(Embeddings):
                    def embed_documents(self, texts):
                        return [[] for _ in texts]

                    def embed_query(self, text):
                        return []

                self._collection = PineconeVectorStore(
                    index=self._get_index(),
                    embedding=_PassthroughEmbedder(),
                    namespace=self.config.collection_name,
                )
            except ImportError:
                raise ImportError(
                    "PineconeVectorStore requires langchain-pinecone. "
                    "Install with: pip install langchain-pinecone"
                )
        return self._collection

    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        vectors = []
        for i, (doc_id, embedding, doc) in enumerate(zip(ids, embeddings, documents)):
            metadata = (metadatas[i] if metadatas else {}) | {"text": doc}
            vectors.append({"id": doc_id, "values": embedding, "metadata": metadata})
        self._get_index().upsert(vectors=vectors, namespace=self.config.collection_name)

    def query_similar(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        query_kwargs: dict = {
            "vector": query_embedding,
            "top_k": n_results,
            "include_metadata": True,
            "include_values": False,
        }
        if where:
            query_kwargs["filter"] = where
        results = self._get_index().query(
            namespace=self.config.collection_name,
            **query_kwargs,
        )
        documents = []
        metadatas = []
        distances = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            documents.append(meta.get("text", ""))
            metadatas.append({k: v for k, v in meta.items() if k != "text"})
            distances.append(match.get("score", 0.0))
        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    def delete(self, ids: list[str]) -> None:
        self._get_index().delete(ids=ids, namespace=self.config.collection_name)

    def count(self) -> int:
        stats = self._get_index().describe_index_stats()
        namespace_stats = stats.get("namespaces", {}).get(self.config.collection_name, {})
        return namespace_stats.get("vector_count", 0)

    def get_or_create_collection(self, name: str | None = None) -> object:
        return self._get_collection()
