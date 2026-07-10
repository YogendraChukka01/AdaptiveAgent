from __future__ import annotations

import logging
from functools import lru_cache

from app.services.retrieval.vector_store.base import BaseVectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_vector_store_config() -> VectorStoreConfig:
    """Build VectorStoreConfig from app settings."""
    from app.core.config import settings

    return VectorStoreConfig(
        store_type=getattr(settings, "vector_store_type", "chroma"),
        collection_name=getattr(settings, "vector_store_collection", "safeagent_docs"),
        chroma_persist_directory=settings.chroma_persist_directory,
        pg_connection_string=getattr(settings, "pgvector_connection_string", ""),
        qdrant_url=getattr(settings, "qdrant_url", "http://localhost:6333"),
        pinecone_api_key=getattr(settings, "pinecone_api_key", ""),
        pinecone_index_name=getattr(settings, "pinecone_index_name", ""),
    )


def get_vector_store() -> BaseVectorStore:
    """Factory: return the configured vector store backend."""
    config = get_vector_store_config()
    store_type = config.store_type.lower()

    if store_type == "pgvector":
        from app.services.retrieval.vector_store.pgvector_store import PGVectorStore

        return PGVectorStore(config)

    if store_type == "qdrant":
        from app.services.retrieval.vector_store.qdrant_store import QdrantVectorStore

        return QdrantVectorStore(config)

    if store_type == "pinecone":
        from app.services.retrieval.vector_store.pinecone_store import PineconeVectorStore

        return PineconeVectorStore(config)

    # Default: ChromaDB
    from app.services.retrieval.vector_store.chroma_store import ChromaVectorStore

    return ChromaVectorStore(config)
