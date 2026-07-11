from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    chunk: str
    relevance_score: float
    page_number: int | None = None


class ToolCallRecord(BaseModel):
    tool: str
    input: str
    output: str | None = None
    success: bool = False
    duration_ms: float = 0.0
    error: str | None = None


class AgentState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    query: str = ""
    sanitized_query: str = ""
    is_safe: bool = False
    safety_issues: list[str] = Field(default_factory=list)
    safety_confidence: float = 0.0

    plan: list[str] = Field(default_factory=list)

    retrieved_docs: list[dict] = Field(default_factory=list)
    retrieval_scores: list[float] = Field(default_factory=list)

    evidence_coverage: float = 0.0
    evidence_contradictions: list[str] = Field(default_factory=list)
    evidence_missing: list[str] = Field(default_factory=list)

    reasoning_path: list[str] = Field(default_factory=list)
    reasoning_method: str = "chain_of_thought"

    confidence_score: float = 0.0
    confidence_factors: dict[str, float] = Field(default_factory=dict)

    risk_score: float = 0.0
    risk_level: str = "low"
    risk_factors: dict[str, float] = Field(default_factory=dict)

    approval_status: str = "pending"

    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    tool_results: list[str] = Field(default_factory=list)

    final_response: str = ""
    citations: list[Citation] = Field(default_factory=list)

    eval_score: float = 0.0
    eval_details: str = ""

    step_count: int = 0
    max_steps: int = 10
    retry_count: int = 0
    refined_query: str = ""
    error: str | None = None
    start_time: float | None = None
