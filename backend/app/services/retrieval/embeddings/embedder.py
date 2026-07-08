from __future__ import annotations

import gc
from functools import lru_cache

import torch
from FlagEmbedding import FlagModel

_embedder: FlagModel | None = None


@lru_cache(maxsize=1)
def get_embedder() -> FlagModel:
    global _embedder
    if _embedder is None:
        _embedder = FlagModel(
            "BAAI/bge-m3",
            query_instruction_for_retrieval="Represent this sentence for searching relevant passages:",
            use_fp16=True,
            devices=["cpu"] if not torch.cuda.is_available() else ["cuda:0"],
        )
    return _embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    embeddings = model.encode(texts)
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
