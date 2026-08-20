from __future__ import annotations

from functools import lru_cache
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.services.retrieval.vector_store.base import BaseVectorStore, VectorStoreConfig


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB vector store backend."""

    def __init__(self, config: VectorStoreConfig) -> None:
        super().__init__(config)
        self._client = chromadb.PersistentClient(
            path=config.chroma_persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        collection = self.get_or_create_collection()
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas or [{} for _ in range(len(ids))],
        )

    def query_similar(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        collection = self.get_or_create_collection()
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where is not None:
            kwargs["where"] = where
        result = collection.query(**kwargs)
        return result if isinstance(result, dict) else {}

    def delete(self, ids: list[str]) -> None:
        collection = self.get_or_create_collection()
        collection.delete(ids=ids)

    def count(self) -> int:
        collection = self.get_or_create_collection()
        result = collection.count()
        return result if isinstance(result, int) else 0

    def get_or_create_collection(self, name: str | None = None) -> Any:
        collection_name = name or self.config.collection_name
        try:
            return self._client.get_collection(collection_name)
        except ValueError:
            try:
                return self._client.create_collection(collection_name)
            except Exception:
                return self._client.get_collection(collection_name)


# ── Legacy compatibility functions (used by upload.py, hybrid_search.py, health.py) ──

_legacy_store: ChromaVectorStore | None = None


def _get_legacy_store() -> ChromaVectorStore:
    global _legacy_store
    if _legacy_store is None:
        _legacy_store = ChromaVectorStore(get_vector_store_config())
    return _legacy_store


@lru_cache(maxsize=1)
def get_chroma_client() -> Any:
    return _get_legacy_store()._client


def get_or_create_collection(name: str = "safeagent_docs") -> Any:
    store = _get_legacy_store()
    return store.get_or_create_collection(name)


def add_documents(
    collection_name: str,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict[str, Any]] | None = None,
) -> None:
    store = _get_legacy_store()
    collection = store.get_or_create_collection(collection_name)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas or [{} for _ in range(len(ids))],
    )


def query_similar(
    collection_name: str,
    query_embedding: list[float],
    n_results: int = 20,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store = _get_legacy_store()
    collection = store.get_or_create_collection(collection_name)
    kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where is not None:
        kwargs["where"] = where
    result = collection.query(**kwargs)
    return result if isinstance(result, dict) else {}


def get_vector_store_config() -> VectorStoreConfig:
    return VectorStoreConfig(
        store_type="chroma",
        chroma_persist_directory=settings.chroma_persist_directory,
    )
