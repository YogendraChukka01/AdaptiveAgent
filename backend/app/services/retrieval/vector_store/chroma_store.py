from __future__ import annotations

from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=settings.chroma_persist_directory,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )


def get_or_create_collection(name: str = "safeagent_docs"):
    client = get_chroma_client()
    try:
        return client.get_collection(name)
    except ValueError:
        return client.create_collection(name)


def add_documents(
    collection_name: str,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict] | None = None,
) -> None:
    collection = get_or_create_collection(collection_name)
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
    where: dict | None = None,
) -> dict:
    collection = get_or_create_collection(collection_name)
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where is not None:
        kwargs["where"] = where
    return collection.query(**kwargs)
