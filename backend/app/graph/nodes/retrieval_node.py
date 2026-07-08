from __future__ import annotations

from app.models.state import AgentState
from app.services.retrieval.embeddings.embedder import embed_query
from app.services.retrieval.hybrid_search import hybrid_search


def retrieval_node(state: AgentState) -> dict:
    query = state.sanitized_query or state.query

    if not query.strip():
        return {"retrieved_docs": [], "retrieval_scores": []}

    query_embedding = embed_query(query)
    results = hybrid_search(query, query_embedding)

    docs = []
    scores = []
    for r in results:
        docs.append(r)
        scores.append(r.get("relevance_score", 0.0))

    return {"retrieved_docs": docs, "retrieval_scores": scores}
