from __future__ import annotations


def calculate_confidence(
    retrieval_scores: list[float],
    evidence_coverage: float,
    num_supporting_docs: int,
) -> tuple[float, dict]:
    factors: dict[str, float] = {}

    if retrieval_scores:
        avg_similarity = sum(retrieval_scores) / len(retrieval_scores)
        factors["retrieval_similarity"] = min(1.0, avg_similarity)
    else:
        factors["retrieval_similarity"] = 0.0

    factors["evidence_coverage"] = evidence_coverage
    factors["document_count"] = min(1.0, num_supporting_docs / 5.0)

    weights = {
        "retrieval_similarity": 0.35,
        "evidence_coverage": 0.35,
        "document_count": 0.30,
    }

    total = sum(
        factors.get(k, 0.0) * v
        for k, v in weights.items()
    )

    confidence = round(total * 100, 1)
    confidence = min(99.9, max(0.0, confidence))

    return confidence, factors
