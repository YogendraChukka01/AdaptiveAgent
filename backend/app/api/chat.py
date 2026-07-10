from __future__ import annotations

import hmac
import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.errors import GraphInterrupt
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from app.core.config import settings
from app.core.deps import get_graph
from app.core.threads import (
    clear_pending_approval,
    track_pending_approval,
)
from app.models.schemas import ApprovalRequest, ChatRequest
from app.models.state import AgentState
from app.services.audit.audit import record_audit
from app.services.memory.memory import memory_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _recursion_limit() -> int:
    """Safely bound graph execution.

    A single retry-loop pass executes ~12 nodes (step_counter -> validator ->
    planner -> tool_planner -> retrieval -> evidence -> reasoning -> confidence
    -> risk -> approval -> tools -> response). With ``max_steps`` allowing up to
    that many loop iterations, the hard recursion limit must sit well above
    ``max_steps * 12`` or LangGraph raises ``GraphRecursionError`` *before* the
    ``step_count`` circuit breaker can stop the loop. The 50 default fails that.
    """
    return max(50, settings.max_steps * 15)


def _unwrap(result) -> dict:
    if isinstance(result, dict):
        return result
    if hasattr(result, "values"):
        return result.values
    return {}


def _build_result(values: dict, thread_id: str) -> dict:
    return {
        "needs_approval": False,
        "thread_id": thread_id,
        "response": values.get("final_response", ""),
        "citations": [
            c.model_dump() if hasattr(c, "model_dump") else c for c in values.get("citations", [])
        ],
        "confidence_score": values.get("confidence_score", 0.0),
        "risk_score": values.get("risk_score", 0.0),
        "risk_level": values.get("risk_level", "low"),
        "reasoning_path": values.get("reasoning_path", []),
        "eval_score": values.get("eval_score", 1.0),
        "eval_details": values.get("eval_details", ""),
        "step_count": values.get("step_count", 0),
        "approval_status": values.get("approval_status", "pending"),
    }


def _build_approval_payload(values: dict, thread_id: str, inter_value: dict | None) -> dict:
    inter_value = inter_value or {}
    return {
        "needs_approval": True,
        "thread_id": thread_id,
        "risk_level": values.get("risk_level"),
        "risk_score": values.get("risk_score"),
        "approval_status": values.get("approval_status"),
        "reason": inter_value.get("reason"),
        "pending_tools": inter_value.get("pending_tools", []),
        "triggering_factors": inter_value.get("triggering_factors", []),
    }


def _extract_interrupt(result: dict | None, snapshot) -> dict | None:
    if isinstance(result, dict):
        interrupts = result.get("__interrupt__")
        if interrupts:
            return interrupts[0].value
    for task in getattr(snapshot, "tasks", ()) or ():
        interrupts = getattr(task, "interrupts", None)
        if interrupts:
            return interrupts[0].value
    return None


async def _stream_events(
    graph: CompiledStateGraph,
    state: AgentState,
    config: dict,
    thread_id: str,
):
    interrupted = False
    try:
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
                    content = chunk.content
                    if isinstance(content, list):
                        text_parts = [
                            b.get("text", "")
                            for b in content
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        content = "".join(text_parts)
                    if content:
                        yield f"event: token\ndata: {json.dumps({'token': content})}\n\n"
    except GraphInterrupt:
        interrupted = True
    except Exception:
        logger.exception("Graph execution failed for thread %s", thread_id)
        yield f"event: error\ndata: {json.dumps({'error': 'Internal error during processing'})}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    snapshot = await graph.aget_state(config)

    if interrupted or snapshot.next:
        inter_value = _extract_interrupt(None, snapshot)
        payload = _build_approval_payload(snapshot.values, thread_id, inter_value)
        await track_pending_approval(
            thread_id,
            payload.get("risk_level"),
            payload.get("risk_score"),
            state.query or "",
        )
        yield f"event: needs_approval\ndata: {json.dumps(payload)}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        return

    values = snapshot.values
    complete_data = json.dumps(_build_result(values, thread_id))
    yield f"event: complete\ndata: {complete_data}\n\n"

    response_text = values.get("final_response", "")
    if response_text:
        await memory_manager.store_conversation(thread_id, "user", state.query or "")
        await memory_manager.store_conversation(thread_id, "assistant", response_text)

    await record_audit(
        {
            "thread_id": thread_id,
            "query": state.query or "",
            "response": response_text,
            "risk_score": values.get("risk_score", 0.0),
            "risk_level": values.get("risk_level", "low"),
            "confidence_score": values.get("confidence_score", 0.0),
            "approval_status": values.get("approval_status", "pending"),
            "tool_calls": [
                t.model_dump() if hasattr(t, "model_dump") else t
                for t in values.get("tool_calls", [])
            ],
            "citations": [
                c.model_dump() if hasattr(c, "model_dump") else c
                for c in values.get("citations", [])
            ],
            "execution_time_ms": (
                int((time.time() - state.start_time) * 1000) if state.start_time else 0
            ),
            "step_count": values.get("step_count", 0),
        }
    )

    yield "event: done\ndata: [DONE]\n\n"


@router.post("")
async def chat(
    request: ChatRequest,
    graph: CompiledStateGraph = Depends(get_graph),
):
    if not request.thread_id:
        request.thread_id = str(uuid.uuid4())
    thread_id = request.thread_id

    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    last_msg = request.messages[-1]
    if "content" not in last_msg or not isinstance(last_msg["content"], str):
        raise HTTPException(
            status_code=400,
            detail="Each message must have a string 'content' field",
        )
    last_message = last_msg["content"]

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": _recursion_limit(),
    }

    history = await memory_manager.get_conversation(thread_id)
    history_messages = []
    for m in history:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "assistant":
            history_messages.append(AIMessage(content=content))
        else:
            history_messages.append(HumanMessage(content=content))

    state = AgentState(
        query=last_message,
        messages=[*history_messages, HumanMessage(content=last_message)],
        step_count=0,
        max_steps=settings.max_steps,
        start_time=time.time(),
    )

    if request.stream:
        return StreamingResponse(
            _stream_events(graph, state, config, thread_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    result = await graph.ainvoke(state, config=config)
    values = _unwrap(result)

    if isinstance(result, dict) and result.get("__interrupt__"):
        snapshot = await graph.aget_state(config)
        inter_value = _extract_interrupt(result, snapshot)
        payload = _build_approval_payload(values, thread_id, inter_value)
        await track_pending_approval(
            thread_id,
            payload.get("risk_level"),
            payload.get("risk_score"),
            last_message,
        )
        return payload

    await memory_manager.store_conversation(thread_id, "user", last_message)
    resp = values.get("final_response", "")
    await memory_manager.store_conversation(thread_id, "assistant", resp)

    await record_audit(
        {
            "thread_id": thread_id,
            "query": last_message,
            "response": values.get("final_response", ""),
            "risk_score": values.get("risk_score", 0.0),
            "risk_level": values.get("risk_level", "low"),
            "confidence_score": values.get("confidence_score", 0.0),
            "approval_status": values.get("approval_status", "pending"),
            "tool_calls": [
                t.model_dump() if hasattr(t, "model_dump") else t
                for t in values.get("tool_calls", [])
            ],
            "citations": [
                c.model_dump() if hasattr(c, "model_dump") else c
                for c in values.get("citations", [])
            ],
            "execution_time_ms": (
                int((time.time() - state.start_time) * 1000) if state.start_time else 0
            ),
            "step_count": values.get("step_count", 0),
        }
    )

    return _build_result(values, thread_id)


async def _require_auth(authorization: str | None = Header(None)):
    if settings.auth_jwt_secret == "change-me-in-production":
        return  # dev mode, no auth
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    if not hmac.compare_digest(token, settings.auth_jwt_secret):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return


@router.post("/approve")
async def approve_action(
    request: ApprovalRequest,
    graph: CompiledStateGraph = Depends(get_graph),
    _auth: None = Depends(_require_auth),
):
    config = {"configurable": {"thread_id": request.thread_id}}

    await graph.ainvoke(
        Command(resume={"approved": request.action == "approve"}),
        config=config,
    )

    await clear_pending_approval(request.thread_id)

    snapshot = await graph.aget_state(config)
    values = snapshot.values

    return _build_result(values, request.thread_id)


@router.get("/pending")
async def list_pending_approvals(
    _auth: None = Depends(_require_auth),
):
    from app.core.threads import list_pending_approvals as _list

    return await _list(include_expired=True)
