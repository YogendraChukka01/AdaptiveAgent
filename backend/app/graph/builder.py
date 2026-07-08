from __future__ import annotations

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.edges.conditional import (
    route_after_approval,
    route_after_confidence,
    route_after_evidence,
    route_after_planner,
    route_after_retrieval,
    route_after_risk,
    route_after_tools,
    route_after_validation,
)
from app.graph.nodes.approval_node import approval_node
from app.graph.nodes.confidence_node import confidence_node
from app.graph.nodes.error_node import error_node
from app.graph.nodes.evidence_node import evidence_node
from app.graph.nodes.planner_node import planner_node
from app.graph.nodes.reasoning_node import reasoning_node
from app.graph.nodes.response_node import response_node
from app.graph.nodes.retrieval_node import retrieval_node
from app.graph.nodes.risk_node import risk_node
from app.graph.nodes.step_counter import step_counter
from app.graph.nodes.tools_node import tools_node
from app.graph.nodes.validator_node import query_validator
from app.models.state import AgentState


def build_graph(checkpointer: AsyncPostgresSaver | None = None) -> CompiledStateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("step_counter", step_counter)
    builder.add_node("validator", query_validator)
    builder.add_node("planner", planner_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("evidence", evidence_node)
    builder.add_node("reasoning", reasoning_node)
    builder.add_node("confidence", confidence_node)
    builder.add_node("risk", risk_node)
    builder.add_node("approval", approval_node)
    builder.add_node("tools", tools_node)
    builder.add_node("response", response_node)
    builder.add_node("error", error_node)

    builder.set_entry_point("step_counter")
    builder.add_edge("step_counter", "validator")

    builder.add_conditional_edges("validator", route_after_validation)
    builder.add_conditional_edges("planner", route_after_planner)
    builder.add_conditional_edges("retrieval", route_after_retrieval)
    builder.add_conditional_edges("evidence", route_after_evidence)
    builder.add_edge("reasoning", "confidence")
    builder.add_conditional_edges("confidence", route_after_confidence)
    builder.add_conditional_edges("risk", route_after_risk)
    builder.add_conditional_edges("approval", route_after_approval)
    builder.add_conditional_edges("tools", route_after_tools)
    builder.add_edge("response", END)
    builder.add_edge("error", END)

    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_after=["approval"] if checkpointer else [],
    )

    return graph
