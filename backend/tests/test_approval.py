from __future__ import annotations

from app.services.approval.approval import determine_approval


def test_low_risk_auto_approve():
    decision = determine_approval(risk_level="low", risk_score=5.0)
    assert decision.status == "approved"
    assert decision.requires_approval is False


def test_medium_risk_auto_approve():
    decision = determine_approval(risk_level="medium", risk_score=50.0)
    assert decision.status == "approved"


def test_high_risk_requires_approval():
    decision = determine_approval(risk_level="high", risk_score=85.0)
    assert decision.status == "pending"
    assert decision.requires_approval is True


def test_high_risk_score_triggers_approval():
    decision = determine_approval(risk_level="low", risk_score=75.0)
    assert decision.requires_approval is True
