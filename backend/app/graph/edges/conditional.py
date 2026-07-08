from __future__ import annotations

from typing import Literal

from app.models.state import AgentState


def route_after_validation(state: AgentState) -> Literal["planner", "error"]:
    if state.error:
        return "error"
    if not state.is_safe:
        return "error"
    return "planner"


def route_after_planner(state: AgentState) -> Literal["retrieval", "response", "error"]:
    if state.error:
        return "error"
    if not state.plan:
        return "response"
    return "retrieval"


def route_after_retrieval(state: AgentState) -> Literal["evidence", "response"]:
    if not state.retrieved_docs:
        return "response"
    return "evidence"


def route_after_evidence(state: AgentState) -> Literal["reasoning", "step_counter", "response"]:
    if state.error:
        return "response"
    if state.evidence_coverage < 0.3 and state.step_count < state.max_steps:
        return "step_counter"
    if not state.evidence_contradictions and state.evidence_coverage >= 0.3:
        return "reasoning"
    return "response"


def route_after_confidence(state: AgentState) -> Literal["risk", "step_counter"]:
    if state.confidence_score < 30.0 and state.step_count < state.max_steps:
        return "step_counter"
    return "risk"


def route_after_risk(state: AgentState) -> Literal["approval", "tools"]:
    return "approval"


def route_after_approval(state: AgentState) -> Literal["tools", "response"]:
    if state.approval_status == "approved" or state.approval_status == "not_required":
        return "tools"
    return "response"


def route_after_tools(state: AgentState) -> Literal["response", "step_counter", "error"]:
    if state.error:
        return "error"
    if state.step_count >= state.max_steps:
        return "response"
    if any(not tc.success for tc in state.tool_calls):
        return "step_counter"
    return "response"


def circuit_breaker(state: AgentState) -> Literal["error", "__end__"]:
    if state.step_count >= state.max_steps:
        return "error"
    return "__end__"
