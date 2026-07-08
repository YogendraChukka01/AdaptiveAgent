from __future__ import annotations

from app.models.state import ToolCallRecord
from app.services.risk.risk import assess_risk


def test_low_risk():
    tool_calls = [ToolCallRecord(tool="web_search", input="test query", success=True)]
    plan = ["retrieve", "analyze"]
    score, level, _ = assess_risk(tool_calls, plan)
    assert level == "low"
    assert score < 30.0


def test_high_risk_delete():
    tool_calls = [ToolCallRecord(tool="delete_database", input="DROP TABLE users", success=False)]
    plan = ["retrieve", "delete"]
    score, level, _ = assess_risk(tool_calls, plan)
    assert level == "high"
    assert score >= 70.0


def test_medium_risk_write():
    tool_calls = [ToolCallRecord(tool="write_file", input="/etc/passwd", success=False)]
    plan = ["retrieve", "write"]
    score, level, _ = assess_risk(tool_calls, plan)
    assert level in ("medium", "high")
