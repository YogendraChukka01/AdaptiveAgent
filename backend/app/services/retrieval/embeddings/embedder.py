from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache

import torch
from FlagEmbedding import FlagModel

from app.core.config import settings

_embedder: object | None = None


@lru_cache(maxsize=1)
def get_embedder() -> object:
    """Build the configured embedding backend.

    - provider "bge"  -> FlagEmbedding BGE-M3 (default, fp16).
    - provider "openai" -> any OpenAI-compatible embeddings API
      (Ollama /v1/embeddings, vLLM, Together, OpenAI, ...).
    """
    global _embedder
    provider = settings.embedding_provider.lower()

    if provider == "openai":
        from app.services.retrieval.embeddings.openai_embedder import (
            OpenAICompatibleEmbedder,
        )

        return OpenAICompatibleEmbedder(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_api_base,
        )

    if _embedder is None:
        _embedder = FlagModel(
            settings.embedding_model,
            query_instruction_for_retrieval=(
                "Represent this sentence for searching relevant passages:"
            ),
            use_fp16=True,
            devices=["cpu"] if not torch.cuda.is_available() else ["cuda:0"],
        )
    return _embedder


_EMBED_CACHE: OrderedDict[tuple[str, ...], list[float]] = OrderedDict()
_EMBED_CACHE_MAX = 2048


def _cache_get(texts: list[str]) -> list[list[float]] | None:
    key = tuple(texts)
    if key in _EMBED_CACHE:
        _EMBED_CACHE.move_to_end(key)
        return _EMBED_CACHE[key]
    return None


def _cache_put(texts: list[str], vectors: list[list[float]]) -> None:
    key = tuple(texts)
    _EMBED_CACHE[key] = vectors
    _EMBED_CACHE.move_to_end(key)
    while len(_EMBED_CACHE) > _EMBED_CACHE_MAX:
        _EMBED_CACHE.popitem(last=False)


def embed_texts(texts: list[str]) -> list[list[float]]:
    cached = _cache_get(texts)
    if cached is not None:
        return cached

    model = get_embedder()
    embeddings = model.encode(texts)
    vectors = embeddings.tolist() if hasattr(embeddings, "tolist") else list(embeddings)
    _cache_put(texts, vectors)
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
