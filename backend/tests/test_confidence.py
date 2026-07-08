from __future__ import annotations

from app.services.confidence.confidence import calculate_confidence


def test_high_confidence():
    score, factors = calculate_confidence(
        retrieval_scores=[0.9, 0.85, 0.8],
        evidence_coverage=0.9,
        num_supporting_docs=3,
    )
    assert score > 70.0
    assert "retrieval_similarity" in factors
    assert "evidence_coverage" in factors


def test_low_confidence():
    score, factors = calculate_confidence(
        retrieval_scores=[0.1],
        evidence_coverage=0.1,
        num_supporting_docs=0,
    )
    assert score < 30.0


def test_empty_retrieval_scores():
    score, factors = calculate_confidence(
        retrieval_scores=[],
        evidence_coverage=0.0,
        num_supporting_docs=0,
    )
    assert score == 0.0
