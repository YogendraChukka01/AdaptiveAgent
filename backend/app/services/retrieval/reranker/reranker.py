from __future__ import annotations

from functools import lru_cache

from FlagEmbedding import FlagReranker

_reranker: FlagReranker | None = None


@lru_cache(maxsize=1)
def get_reranker() -> FlagReranker:
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker(
            "BAAI/bge-reranker-v2-m3",
            use_fp16=True,
        )
    return _reranker


def rerank(
    query: str,
    documents: list[str],
    top_k: int = 5,
) -> list[tuple[str, float, int]]:
    reranker = get_reranker()
    pairs = [[query, doc] for doc in documents]
    scores = reranker.compute_score(pairs)

    indexed = [(documents[i], scores[i], i) for i in range(len(documents))]
    indexed.sort(key=lambda x: x[1], reverse=True)
    return [(doc, score, idx) for doc, score, idx in indexed[:top_k]]
