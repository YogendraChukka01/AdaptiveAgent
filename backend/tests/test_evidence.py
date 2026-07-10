from __future__ import annotations

from app.services.evidence.evidence import verify_evidence


def test_no_documents():
    result = verify_evidence("capital of France", [])
    assert result["covered"] is False
    assert result["coverage_score"] == 0.0
    assert "No documents retrieved" in result["missing"]


def test_low_relevance_docs():
    docs = [
        {
            "content": "Paris is the capital of France",
            "relevance_score": 0.1,
            "source": "wiki",
        }
    ]
    result = verify_evidence("capital of France", docs)
    assert result["covered"] is False
    assert result["coverage_score"] == 0.0


def test_full_coverage():
    docs = [
        {
            "content": ("Paris is the capital city of France located on the Seine river"),
            "relevance_score": 0.9,
            "source": "en.wikipedia.org",
        },
        {
            "content": ("France borders Germany and Spain and has many famous landmarks"),
            "relevance_score": 0.85,
            "source": "britannica.com",
        },
        {
            "content": "The capital of France is Paris a major European city",
            "relevance_score": 0.8,
            "source": "wiki",
        },
    ]
    result = verify_evidence("capital of France", docs)
    assert result["covered"] is True
    assert result["coverage_score"] > 0.4
    assert result["credible"] is True
    assert len(result["contradictions"]) == 0


def test_contradiction_detected():
    docs = [
        {
            "content": (
                "Paris is the capital of France. It is located in the north of the country."
            ),
            "relevance_score": 0.9,
            "source": "wiki",
        },
        {
            "content": ("Paris is not the capital of France. The capital was moved to Lyon."),
            "relevance_score": 0.85,
            "source": "blog",
        },
    ]
    result = verify_evidence("capital of France", docs)
    assert any("negates" in c.lower() for c in result["contradictions"])


def test_credible_source_boost():
    docs = [
        {
            "content": "Paris is the capital of France",
            "relevance_score": 0.9,
            "source": "en.wikipedia.org",
        }
    ]
    result = verify_evidence("capital of France", docs)
    assert result["credible"] is True


def test_non_credible_source():
    docs = [
        {
            "content": "Paris is the capital of France",
            "relevance_score": 0.9,
            "source": "randomblog.xyz",
        }
    ]
    result = verify_evidence("capital of France", docs)
    assert result["credible"] is False


def test_missing_terms_reported():
    docs = [{"content": "Berlin has many museums", "relevance_score": 0.8, "source": "wiki"}]
    result = verify_evidence("population Berlin Germany", docs)
    missing = " ".join(result["missing"]).lower()
    assert "population" in missing or "germany" in missing


def test_contradiction_requires_shared_terms():
    docs = [
        {
            "content": "The economy grew by 2 percent last quarter.",
            "relevance_score": 0.9,
            "source": "report",
        },
        {
            "content": "The best pizza toppings are pepperoni and mushrooms.",
            "relevance_score": 0.85,
            "source": "blog",
        },
    ]
    result = verify_evidence("economy", docs)
    assert len(result["contradictions"]) == 0
