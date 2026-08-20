from __future__ import annotations

import hashlib
import logging
import threading
from typing import Any

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.services.retrieval.reranker.reranker import rerank
from app.services.retrieval.vector_store.factory import get_vector_store

logger = logging.getLogger(__name__)

# ── BM25 index cache ──────────────────────────────────────────────────────────
# Key: (collection_name, fingerprint_of_doc_texts)
# The fingerprint is an MD5 of joined doc texts, so the cache is automatically
# invalidated whenever the document corpus changes (e.g. after an upload).
_BM25_CACHE: dict[tuple[str, str], BM25Retriever] = {}
_BM25_LOCK = threading.Lock()
_BM25_CACHE_MAX = 8  # keep at most 8 different corpora cached


def _doc_fingerprint(documents: list[str]) -> str:
    """Cheap stable fingerprint of a document corpus for cache keying."""
    h = hashlib.md5(usedforsecurity=False)
    for doc in documents:
        h.update(doc[:200].encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _get_bm25(collection_name: str, documents: list[str], k: int) -> BM25Retriever:
    fp = _doc_fingerprint(documents)
    cache_key = (collection_name, fp)
    with _BM25_LOCK:
        if cache_key in _BM25_CACHE:
            retriever = _BM25_CACHE[cache_key]
            retriever.k = k
            return retriever
        # Evict oldest entry if over limit
        while len(_BM25_CACHE) >= _BM25_CACHE_MAX:
            _BM25_CACHE.pop(next(iter(_BM25_CACHE)))
        docs = [Document(page_content=d, metadata={"idx": i}) for i, d in enumerate(documents)]
        retriever = BM25Retriever.from_documents(docs, k=k)
        _BM25_CACHE[cache_key] = retriever
        return retriever


def hybrid_search(
    query: str,
    query_embedding: list[float],
    collection_name: str = "safeagent_docs",
    dense_k: int = 20,
    final_k: int = 5,
) -> list[dict[str, Any]]:
    """Hybrid dense + BM25 + rerank retrieval, routed through the configured
    vector store backend (Chroma / pgvector / Qdrant / Pinecone).

    Changes vs old implementation:
    - Uses vector store factory instead of hardcoding ChromaDB.
    - BM25 index is cached per (collection, corpus-fingerprint) so it is NOT
      rebuilt from scratch on every request.
    """
    # ── Dense retrieval via configured vector store ───────────────────────────
    try:
        store = get_vector_store()
        chroma_results = store.query_similar(
            query_embedding=query_embedding,
            n_results=dense_k,
        )
    except Exception:
        logger.exception("Dense retrieval failed")
        return []

    if not chroma_results or not chroma_results.get("documents"):
        return []

    raw_docs = chroma_results["documents"]
    # Some backends return [[...]] (list of lists), others return [...].
    documents: list[str] = raw_docs[0] if raw_docs and isinstance(raw_docs[0], list) else raw_docs
    metadatas_raw = chroma_results.get("metadatas") or []
    metadatas: list[dict[str, Any]] = (
        metadatas_raw[0]
        if metadatas_raw and isinstance(metadatas_raw[0], list)
        else metadatas_raw
    ) or [{} for _ in documents]
    distances_raw = chroma_results.get("distances") or []
    distances: list[float] = (
        distances_raw[0]
        if distances_raw and isinstance(distances_raw[0], list)
        else distances_raw
    ) or [0.0] * len(documents)

    if not documents:
        return []

    # ── BM25 sparse retrieval (cached) ────────────────────────────────────────
    bm25 = _get_bm25(collection_name, documents, k=dense_k)
    bm25_hits = bm25.invoke(query)
    bm25_indices = {d.metadata["idx"] for d in bm25_hits}

    # Merge: BM25 hits first (preferred), then remaining dense-only docs
    merged_texts: list[str] = []
    merged_indices: list[int] = []
    for d in bm25_hits:
        idx = d.metadata["idx"]
        merged_texts.append(documents[idx])
        merged_indices.append(idx)
    for i, doc_text in enumerate(documents):
        if i not in bm25_indices:
            merged_texts.append(doc_text)
            merged_indices.append(i)

    # ── Rerank ────────────────────────────────────────────────────────────────
    reranked = rerank(query, merged_texts, top_k=final_k)

    results = []
    for doc_text, score, idx in reranked:
        original_idx = merged_indices[idx] if idx < len(merged_indices) else idx
        meta = metadatas[original_idx] if original_idx < len(metadatas) else {}
        results.append(
            {
                "content": doc_text,
                "relevance_score": float(score),
                "source": meta.get("source", "unknown"),
                "page": meta.get("page"),
                "dense_distance": (
                    float(distances[original_idx]) if original_idx < len(distances) else 0.0
                ),
            }
        )

    return results
