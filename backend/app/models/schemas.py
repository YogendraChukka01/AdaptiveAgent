from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    thread_id: str = ""
    stream: bool = True


class ChatResponse(BaseModel):
    response: str
    citations: list[dict] = Field(default_factory=list)
    confidence_score: float = 0.0
    risk_score: float = 0.0
    risk_level: str = "low"
    reasoning_path: list[str] = Field(default_factory=list)
    step_count: int = 0


class ApprovalRequest(BaseModel):
    thread_id: str
    action: str = Field(pattern="^(approve|reject)$")


class UploadRequest(BaseModel):
    thread_id: str = ""


class AuditEntry(BaseModel):
    id: str
    thread_id: str
    query: str
    response: str
    risk_score: float
    approval_status: str
    execution_time_ms: float
    created_at: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    ollama_connected: bool = False
    chroma_connected: bool = False
    db_connected: bool = False
