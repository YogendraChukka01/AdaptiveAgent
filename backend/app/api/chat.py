from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from app.core.config import settings
from app.core.deps import get_graph
from app.models.schemas import ApprovalRequest, ChatRequest
from app.models.state import AgentState
from app.services.audit.audit import record_audit
from app.services.memory.memory import memory_manager

router = APIRouter(prefix="/chat", tags=["chat"])


async def _stream_events(
    graph: CompiledStateGraph,
    state: AgentState,
    config: dict,
    thread_id: str,
    history: list | None = None,
):
    async for event in graph.astream_events(
        state,
        config=config,
        version="v2",
    ):
        kind = event.get("event", "")
        if kind == "on_chain_start":
            node = event.get("name", "")
            yield f"event: node_start\ndata: {json.dumps({'node': node})}\n\n"
        elif kind == "on_chain_end":
            node = event.get("name", "")
            yield f"event: node_end\ndata: {json.dumps({'node': node})}\n\n"
        elif kind == "on_chat_model_stream":
            data = event.get("data", {})
            chunk = data.get("chunk", "")
            if chunk and hasattr(chunk, "content"):
                yield f"event: token\ndata: {json.dumps({'token': chunk.content})}\n\n"

    final_state = await graph.aget_state(config)
    result = final_state.values

    complete_data = json.dumps({
        'response': result.get('final_response', ''),
        'confidence_score': result.get('confidence_score', 0.0),
        'risk_score': result.get('risk_score', 0.0),
        'risk_level': result.get('risk_level', 'low'),
        'reasoning_path': result.get('reasoning_path', []),
        'citations': [
            c.model_dump() if hasattr(c, 'model_dump') else c
            for c in result.get('citations', [])
        ],
        'step_count': result.get('step_count', 0),
    })
    yield f"event: complete\ndata: {complete_data}\n\n"

    response_text = result.get('final_response', '')
    if response_text:
        await memory_manager.store_conversation(thread_id, "user", state.query or "")
        await memory_manager.store_conversation(thread_id, "assistant", response_text)

    await record_audit({
        "thread_id": thread_id,
        "query": state.query or "",
        "response": response_text,
        "risk_score": result.get("risk_score", 0.0),
        "risk_level": result.get("risk_level", "high"),
        "confidence_score": result.get("confidence_score", 0.0),
        "approval_status": result.get("approval_status", "pending"),
        "tool_calls": [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in result.get("tool_calls", [])
        ],
        "citations": [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in result.get("citations", [])
        ],
        "execution_time_ms": (
            int((time.time() - state.start_time) * 1000) if state.start_time else 0
        ),
        "step_count": result.get("step_count", 0),
    })

    yield "event: done\ndata: [DONE]\n\n"


@router.post("")
async def chat(
    request: ChatRequest,
    graph: CompiledStateGraph = Depends(get_graph),
):
    thread_id = request.thread_id
    last_message = request.messages[-1]["content"] if request.messages else ""

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }

    history = await memory_manager.get_conversation(thread_id)
    history_messages = [
        HumanMessage(content=m["content"])
        for m in history
    ]

    state = AgentState(
        query=last_message,
        messages=[*history_messages, HumanMessage(content=last_message)],
        step_count=0,
        max_steps=10,
        start_time=time.time(),
    )

    if request.stream:
        return StreamingResponse(
            _stream_events(graph, state, config, thread_id, history),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    final_state = await graph.ainvoke(state, config=config)
    if isinstance(final_state, dict):
        result = final_state
    elif hasattr(final_state, "values"):
        result = final_state.values
    else:
        result = {}

    await memory_manager.store_conversation(thread_id, "user", last_message)
    resp = result.get("final_response", "")
    await memory_manager.store_conversation(thread_id, "assistant", resp)

    await record_audit({
        "thread_id": thread_id,
        "query": last_message,
        "response": result.get("final_response", ""),
        "risk_score": result.get("risk_score", 0.0),
        "risk_level": result.get("risk_level", "high"),
        "confidence_score": result.get("confidence_score", 0.0),
        "approval_status": result.get("approval_status", "pending"),
        "tool_calls": [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in result.get("tool_calls", [])
        ],
        "citations": [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in result.get("citations", [])
        ],
        "execution_time_ms": (
            int((time.time() - state.start_time) * 1000) if state.start_time else 0
        ),
        "step_count": result.get("step_count", 0),
    })

    return {
        "response": result.get("final_response", ""),
        "citations": result.get("citations", []),
        "confidence_score": result.get("confidence_score", 0.0),
        "risk_score": result.get("risk_score", 0.0),
        "risk_level": result.get("risk_level", "low"),
        "reasoning_path": result.get("reasoning_path", []),
        "step_count": result.get("step_count", 0),
    }


async def _require_auth(authorization: str | None = Header(None)):
    if settings.auth_jwt_secret == "change-me-in-production":
        return  # dev mode, no auth
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    if token != settings.auth_jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return


@router.post("/approve")
async def approve_action(
    request: ApprovalRequest,
    graph: CompiledStateGraph = Depends(get_graph),
    _auth: None = Depends(_require_auth),
):
    config = {"configurable": {"thread_id": request.thread_id}}

    approved = request.action == "approve"
    graph.invoke(Command(resume={"approved": approved}), config=config)

    final_state = await graph.aget_state(config)
    result = final_state.values

    return {
        "status": "approved" if approved else "rejected",
        "response": result.get("final_response", ""),
    }
