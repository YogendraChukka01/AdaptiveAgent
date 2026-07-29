from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class VectorStoreConfig(BaseModel):
    """Configuration for any vector store backend."""

    store_type: str = "chroma"
    collection_name: str = "safeagent_docs"

    # ChromaDB
    chroma_persist_directory: str = "./chroma_data"

    # PGVector
    pg_connection_string: str = ""
    pg_table_name: str = "langchain"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_grpc: bool = False

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""


class BaseVectorStore(ABC):
    """Store-agnostic abstraction for vector backends."""

    def __init__(self, config: VectorStoreConfig) -> None:
        self.config = config

    @abstractmethod
    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add documents with pre-computed embeddings."""

    @abstractmethod
    def query_similar(
        self,
        query_embedding: list[float],
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        """Query similar documents. Returns dict with documents, metadatas, distances."""

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""

    @abstractmethod
    def count(self) -> int:
        """Return total document count."""

    @abstractmethod
    def get_or_create_collection(self, name: str | None = None) -> Any:
        """Return underlying native collection handle."""
