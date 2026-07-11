from __future__ import annotations

from functools import lru_cache

from FlagEmbedding import FlagReranker

from app.core.config import settings


@lru_cache(maxsize=1)
def get_reranker():
    """Build the configured reranker backend.

    - provider "bge" -> FlagEmbedding BGE reranker (default).
    - provider "rest" -> any Jina/Cohere/Voyage-shaped rerank API
      (set ``reranker_api_base``).
    """
    provider = settings.reranker_provider.lower()

    if provider == "rest":
        from app.services.retrieval.reranker.rest_reranker import RestReranker

        return RestReranker(
            model=settings.reranker_model or "rerank-v2",
            api_base=settings.reranker_api_base,
            api_key=settings.reranker_api_key,
        )

    return FlagReranker(
        settings.ollama_reranker_model,
        use_fp16=True,
    )


def rerank(
    query: str,
    documents: list[str],
    top_k: int = 5,
) -> list[tuple[str, float, int]]:
    reranker = get_reranker()
    pairs = [[query, doc] for doc in documents]
    scores = reranker.compute_score(pairs)

    if not isinstance(scores, list):
        scores = [scores]

    indexed = [(documents[i], scores[i], i) for i in range(len(documents))]
    indexed.sort(key=lambda x: x[1], reverse=True)
    return [(doc, score, idx) for doc, score, idx in indexed[:top_k]]
