from __future__ import annotations

from typing import Literal

from app.core.config import settings
from app.models.state import AgentState


def route_after_validation(state: AgentState) -> Literal["planner", "error"]:
    if state.error:
        return "error"
    if not state.is_safe:
        return "error"
    return "planner"


def route_after_planner(state: AgentState) -> Literal["tool_planner", "response", "error"]:
    if state.error:
        return "error"
    if not state.plan:
        return "response"
    return "tool_planner"


def route_after_retrieval(state: AgentState) -> Literal["evidence", "response"]:
    if not state.retrieved_docs:
        return "response"
    return "evidence"


def route_after_evidence(state: AgentState) -> Literal["reasoning", "refine", "error"]:
    if state.error:
        return "error"
    if state.evidence_coverage < settings.evidence_threshold and state.step_count < state.max_steps:
        return "refine"
    return "reasoning"


def route_after_confidence(state: AgentState) -> Literal["risk", "refine"]:
    if (
        state.confidence_score < settings.confidence_retry_threshold
        and state.step_count < state.max_steps
    ):
        return "refine"
    return "risk"


def route_after_risk(state: AgentState) -> Literal["approval"]:
    return "approval"


def route_after_approval(state: AgentState) -> Literal["tools", "response"]:
    if state.approval_status == "approved" or state.approval_status == "not_required":
        return "tools"
    return "response"


def route_after_tools(state: AgentState) -> Literal["response", "refine", "error"]:
    if state.error:
        return "error"
    if state.step_count >= state.max_steps:
        return "response"
    if any(not tc.success for tc in state.tool_calls):
        return "refine"
    return "response"
