from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes.confidence_node import confidence_node
from app.graph.nodes.evidence_node import evidence_node
from app.graph.nodes.planner_node import planner_node
from app.graph.nodes.refine_node import refine_node
from app.graph.nodes.response_node import response_node
from app.graph.nodes.risk_node import risk_node
from app.graph.nodes.validator_node import query_validator
from app.models.state import AgentState


@pytest.fixture
def test_graph():
    builder = StateGraph(AgentState)
    builder.add_node("validator", query_validator)
    builder.add_node("planner", planner_node)
    builder.add_node("evidence", evidence_node)
    builder.add_node("confidence", confidence_node)
    builder.add_node("risk", risk_node)
    builder.add_node("response", response_node)
    builder.set_entry_point("validator")
    builder.add_edge("validator", "planner")
    builder.add_edge("planner", "evidence")
    builder.add_edge("evidence", "confidence")
    builder.add_edge("confidence", "risk")
    builder.add_edge("risk", "response")
    builder.add_edge("response", END)
    return builder.compile()


@pytest.mark.asyncio
async def test_graph_execution(test_graph: CompiledStateGraph):
    state = AgentState(
        query="What is the capital of France?",
        messages=[],
    )
    result = await test_graph.ainvoke(state)
    assert result is not None
    assert hasattr(result, "values") or isinstance(result, dict)


def test_refine_node_rewrites_query(monkeypatch):
    import app.graph.nodes.refine_node as refine_node_mod

    def fake_llm(*a, **k):
        class _M:
            def invoke(self, msgs):
                return HumanMessage(content="rewritten query")

        return _M()

    monkeypatch.setattr(refine_node_mod, "get_llm", fake_llm)

    state = AgentState(
        query="original question",
        sanitized_query="original question",
        step_count=3,
        retry_count=0,
        evidence_missing=["population", "gdp"],
    )
    out = refine_node(state)

    assert out["retry_count"] == 1
    assert out["step_count"] == 4  # circuit breaker keeps counting
    assert out["sanitized_query"] == "rewritten query"
    assert out["refined_query"] == "rewritten query"


def test_refine_node_deterministic_fallback(monkeypatch):
    import app.graph.nodes.refine_node as refine_node_mod

    def boom(*a, **k):
        raise RuntimeError("llm down")

    monkeypatch.setattr(refine_node_mod, "get_llm", boom)

    # With no missing terms the fallback broadens the query.
    out = refine_node(AgentState(query="q", sanitized_query="q", step_count=1, retry_count=2))
    assert out["sanitized_query"] == "q overview"
    assert out["retry_count"] == 3

    # Missing terms bias the query toward what was absent.
    out2 = refine_node(
        AgentState(
            query="q",
            sanitized_query="q",
            step_count=1,
            retry_count=1,
            evidence_missing=["population"],
        )
    )
    assert "population" in out2["sanitized_query"]
