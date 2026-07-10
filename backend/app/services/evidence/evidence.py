from __future__ import annotations

import re

from app.core.config import settings


def _extract_key_terms(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z]\w+", text.lower())
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "shall",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "because",
        "and",
        "but",
        "or",
        "if",
        "while",
        "that",
        "this",
        "these",
        "those",
        "it",
        "its",
        "what",
        "which",
        "who",
        "whom",
    }
    return {w for w in words if w not in stopwords and len(w) > 2}


def _compute_contradictions(
    documents: list[dict],
    threshold: float,
) -> list[str]:
    contradictions: list[str] = []
    texts = [d.get("content", "") for d in documents]
    terms_list = [_extract_key_terms(t) for t in texts]

    for i in range(len(documents)):
        for j in range(i + 1, len(documents)):
            overlap = terms_list[i] & terms_list[j]
            if len(overlap) <= 2:
                continue

            source_i = documents[i].get("source", f"doc_{i}")
            source_j = documents[j].get("source", f"doc_{j}")

            lower_i = texts[i].lower()
            lower_j = texts[j].lower()

            for term in overlap:
                neg_i = re.search(rf"\bnot\b.{{0,20}}\b{term}\b", lower_i)
                neg_i = neg_i or re.search(rf"\b{term}\b.{{0,20}}\bnot\b", lower_i)
                neg_j = re.search(rf"\bnot\b.{{0,20}}\b{term}\b", lower_j)
                neg_j = neg_j or re.search(rf"\b{term}\b.{{0,20}}\bnot\b", lower_j)
                negated_i = neg_i
                negated_j = neg_j
                if negated_i and not negated_j:
                    contradictions.append(
                        f"{source_i} negates '{term}' while {source_j} affirms it"
                    )
                    break
                if negated_j and not negated_i:
                    contradictions.append(
                        f"{source_j} negates '{term}' while {source_i} affirms it"
                    )
                    break
    return contradictions


def _score_credibility(documents: list[dict]) -> float:
    if not documents:
        return 0.0
    credible_sources = {"arxiv", "pubmed", "wikipedia", "gov", "edu", "nature", "science"}
    scores = []
    for d in documents:
        source = d.get("source", "").lower()
        score = 0.3
        for keyword in credible_sources:
            if keyword in source:
                score = 0.9
                break
        if d.get("page"):
            score = min(1.0, score + 0.1)
        scores.append(score)
    return sum(scores) / len(scores)


def verify_evidence(
    query: str,
    documents: list[dict],
    confidence_threshold: float | None = None,
) -> dict:
    threshold = (
        confidence_threshold if confidence_threshold is not None else settings.evidence_threshold
    )

    if not documents:
        return {
            "covered": False,
            "coverage_score": 0.0,
            "contradictions": [],
            "missing": ["No documents retrieved"],
            "credible": False,
        }

    relevant_docs = [d for d in documents if d.get("relevance_score", 0) >= threshold]

    query_terms = _extract_key_terms(query)
    missing_terms: list[str] = []
    doc_term_coverage: list[float] = []

    for d in relevant_docs:
        content = d.get("content", "")
        doc_terms = _extract_key_terms(content)
        if query_terms:
            covered = query_terms & doc_terms
            ratio = len(covered) / len(query_terms)
            doc_term_coverage.append(ratio)
            uncovered = query_terms - doc_terms
            missing_terms.extend(uncovered)
        else:
            doc_term_coverage.append(0.0)

    missing_terms = list(set(missing_terms))
    avg_term_coverage = sum(doc_term_coverage) / max(len(doc_term_coverage), 1)
    doc_count_score = min(1.0, len(relevant_docs) / float(settings.evidence_min_docs))

    contradictions = _compute_contradictions(relevant_docs, threshold)
    credibility = _score_credibility(relevant_docs)

    weights = settings.evidence_weights
    coverage_score = (
        avg_term_coverage * weights["term_coverage"]
        + doc_count_score * weights["doc_count"]
        + credibility * weights["credibility"]
    )
    coverage_score = max(0.0, min(1.0, coverage_score))

    return {
        "covered": coverage_score >= settings.evidence_min_coverage,
        "coverage_score": round(coverage_score, 3),
        "contradictions": contradictions,
        "missing": missing_terms[:10],
        "credible": credibility >= 0.4,
    }
