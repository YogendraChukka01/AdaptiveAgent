from __future__ import annotations

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.services.retrieval.reranker.reranker import rerank
from app.services.retrieval.vector_store.chroma_store import query_similar


def hybrid_search(
    query: str,
    query_embedding: list[float],
    collection_name: str = "safeagent_docs",
    dense_k: int = 20,
    final_k: int = 5,
) -> list[dict]:
    chroma_results = query_similar(
        collection_name=collection_name,
        query_embedding=query_embedding,
        n_results=dense_k,
    )

    if not chroma_results or not chroma_results.get("documents"):
        return []

    documents = chroma_results["documents"][0]
    metadatas = (
        chroma_results["metadatas"][0]
        if chroma_results.get("metadatas")
        else [{}] * len(documents)
    )
    distances = (
        chroma_results["distances"][0]
        if chroma_results.get("distances")
        else [0.0] * len(documents)
    )

    if not documents:
        return []

    docs = [
        Document(page_content=documents[i], metadata={"idx": i})
        for i in range(len(documents))
    ]

    bm25 = BM25Retriever.from_documents(docs, k=dense_k)
    bm25_hits = bm25.invoke(query)
    bm25_indices = {d.metadata["idx"] for d in bm25_hits}

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

    reranked = rerank(query, merged_texts, top_k=final_k)

    results = []
    for doc_text, score, idx in reranked:
        original_idx = merged_indices[idx]
        meta = metadatas[original_idx] if original_idx < len(metadatas) else {}
        results.append({
            "content": doc_text,
            "relevance_score": float(score),
            "source": meta.get("source", "unknown"),
            "page": meta.get("page"),
            "dense_distance": (
                float(distances[original_idx])
                if original_idx < len(distances)
                else 0.0
            ),
        })

    return results
