from __future__ import annotations

import pytest
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes.confidence_node import confidence_node
from app.graph.nodes.evidence_node import evidence_node
from app.graph.nodes.planner_node import planner_node
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
