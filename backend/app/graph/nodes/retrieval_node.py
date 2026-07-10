from __future__ import annotations

import logging

from app.models.state import AgentState
from app.services.retrieval.embeddings.embedder import embed_query
from app.services.retrieval.hybrid_search import hybrid_search

logger = logging.getLogger(__name__)


def retrieval_node(state: AgentState) -> dict:
    query = state.sanitized_query or state.query

    if not query.strip():
        return {"retrieved_docs": [], "retrieval_scores": []}

    # On retries, widen the candidate surface area (CRAG: don't optimise k too
    # early). More candidates => a better chance the reranker keeps relevant ones.
    dense_k = 20 + state.retry_count * 10
    final_k = min(5 + state.retry_count * 3, 20)

    try:
        query_embedding = embed_query(query)
        results = hybrid_search(query, query_embedding, dense_k=dense_k, final_k=final_k)
    except Exception:
        logger.exception("Retrieval failed for query: %s", query[:100])
        return {"retrieved_docs": [], "retrieval_scores": []}

    docs = []
    scores = []
    for r in results:
        docs.append(r)
        scores.append(r.get("relevance_score", 0.0))

    return {"retrieved_docs": docs, "retrieval_scores": scores}
