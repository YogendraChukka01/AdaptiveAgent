from __future__ import annotations

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


def test_bm25_basic():
    docs = [
        Document(page_content="The capital of France is Paris"),
        Document(page_content="Berlin is the capital of Germany"),
        Document(page_content="London is the capital of the United Kingdom"),
        Document(page_content="Python is a programming language"),
    ]
    bm25 = BM25Retriever.from_documents(docs, k=2)
    results = bm25.invoke("capital of France")
    assert len(results) >= 1
    assert any("Paris" in d.page_content for d in results)


def test_bm25_no_match_returns_all():
    docs = [
        Document(page_content="Python programming"),
        Document(page_content="Machine learning"),
    ]
    bm25 = BM25Retriever.from_documents(docs, k=5)
    results = bm25.invoke("zzzzzxxxxx")
    assert len(results) == 2
