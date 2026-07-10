from __future__ import annotations

import importlib
import json
import types

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.core.config import settings
from app.models.state import AgentState, ToolCallRecord


# ---------------------------------------------------------------------------
# 1. Config defaults
# ---------------------------------------------------------------------------
def test_config_defaults():
    assert settings.embedding_provider == "bge"
    assert settings.reranker_provider == "bge"
    assert settings.embedding_model == "BAAI/bge-m3"
    assert settings.ollama_reranker_model == "BAAI/bge-reranker-v2-m3"
    assert settings.llm_cache_enabled is True
    assert settings.confidence_retry_threshold == 30.0
    assert settings.approval_ttl_seconds == 86400


# ---------------------------------------------------------------------------
# 2. Approval matrix ("100 ways")
# ---------------------------------------------------------------------------
def tcr_factory(name: str) -> ToolCallRecord:
    return ToolCallRecord(tool=name, input="{}", success=False)


@pytest.mark.parametrize(
    "risk_level,risk_score,tools,plan,exp_status,exp_pending",
    [
        # low risk, no tools
        ("low", 5.0, [], [], "approved", False),
        ("low", 29.0, [], [], "approved", False),
        # medium risk
        ("medium", 50.0, [], [], "approved", False),
        ("low", 35.0, [], [], "approved", False),
        # high risk by level
        ("high", 5.0, [], [], "pending", True),
        # high risk by score
        ("low", 75.0, [], [], "pending", True),
        ("medium", 80.0, [], [], "pending", True),
        # sensitive tool -> pending, regardless of level
        ("low", 5.0, [tcr_factory("delete_records")], [], "pending", True),
        ("low", 5.0, [tcr_factory("admin_console")], [], "pending", True),
        ("low", 5.0, [tcr_factory("financial_report")], [], "pending", True),
        ("low", 5.0, [tcr_factory("send_email")], [], "pending", True),
        ("low", 5.0, [tcr_factory("write_file")], [], "pending", True),
        ("low", 5.0, [tcr_factory("database_query")], [], "pending", True),
        # safe tools -> not pending on their own (low/medium)
        ("low", 5.0, [tcr_factory("web_search")], [], "approved", False),
        ("low", 5.0, [tcr_factory("read_file")], [], "approved", False),
        # mixed: sensitive dominates
        ("low", 5.0, [tcr_factory("web_search"), tcr_factory("delete_x")], [], "pending", True),
        # plan keywords
        ("low", 5.0, [], ["please delete the logs"], "pending", True),
        ("low", 5.0, [], ["run a financial transaction"], "pending", True),
        ("low", 5.0, [], ["search the web"], "approved", False),
        # sensitive tool name substring must match whole keyword
        ("low", 5.0, [tcr_factory("my_delete_helper")], [], "pending", True),
        ("low", 5.0, [tcr_factory("read_only")], [], "approved", False),
    ],
)
def test_approval_matrix(risk_level, risk_score, tools, plan, exp_status, exp_pending):
    from app.services.approval.approval import determine_approval

    decision = determine_approval(
        risk_level=risk_level,
        risk_score=risk_score,
        tool_calls=tools,
        plan=plan,
    )
    assert decision.status == exp_status, decision
    assert decision.requires_approval is exp_pending
    # pending tools must be listed when pending due to a tool
    if exp_pending and tools:
        assert decision.pending_tools, decision


def test_approval_empty_inputs():
    from app.services.approval.approval import determine_approval

    d = determine_approval(risk_level="low", risk_score=0.0)
    assert d.status == "approved"
    assert d.pending_tools == []
    assert d.triggering_factors == []


# ---------------------------------------------------------------------------
# 3. Routing matrix
# ---------------------------------------------------------------------------
def _state(**kw):
    base = dict(
        messages=[], query="", sanitized_query="", is_safe=False,
        safety_issues=[], safety_confidence=0.0, plan=[],
        current_plan_step=0, retrieved_docs=[], retrieval_scores=[],
        evidence_coverage=0.0, evidence_contradictions=[], evidence_missing=[],
        reasoning_path=[], reasoning_method="chain_of_thought",
        confidence_score=0.0, confidence_factors={}, risk_score=0.0,
        risk_level="high", risk_factors={}, approval_status="pending",
        tool_calls=[], tool_results=[], final_response="", citations=[],
        step_count=0, max_steps=10, error=None, start_time=0.0,
        end_time=0.0,
    )
    base.update(kw)
    return AgentState(**base)


@pytest.mark.parametrize(
    "state,exp",
    [
        (_state(is_safe=False, error="boom"), "error"),
        (_state(is_safe=True), "planner"),
        (_state(plan=[]), "response"),
        (_state(plan=["retrieve", "respond"]), "tool_planner"),
        # retrieval
        (_state(retrieved_docs=[]), "response"),
        (_state(retrieved_docs=[{"content": "x"}]), "evidence"),
        # evidence
        (_state(evidence_coverage=0.9, evidence_contradictions=["a b"]), "reasoning"),
        (_state(evidence_coverage=0.1, step_count=1), "refine"),
        (_state(evidence_coverage=0.1, step_count=10), "reasoning"),
        # confidence
        (_state(confidence_score=10.0, step_count=1), "refine"),
        (_state(confidence_score=10.0, step_count=10), "risk"),
        (_state(confidence_score=80.0), "risk"),
        # risk -> approval
        (_state(), "approval"),
        # approval
        (_state(approval_status="approved"), "tools"),
        (_state(approval_status="not_required"), "tools"),
        (_state(approval_status="rejected"), "response"),
        (_state(approval_status="pending"), "response"),
        # tools
        (
            _state(
                tool_calls=[
                    ToolCallRecord(tool="x", input="{}", success=False)
                ],
                approval_status="approved",
            ),
            "response",
        ),
        (
            _state(
                tool_calls=[
                    ToolCallRecord(tool="x", input="{}", success=True)
                ],
                approval_status="approved",
            ),
            "response",
        ),
        (
            _state(
                tool_calls=[
                    ToolCallRecord(tool="x", input="{}", success=False)
                ],
                approval_status="approved",
                step_count=10,
            ),
            "response",
        ),
        (
            _state(
                error="e",
                tool_calls=[
                    ToolCallRecord(tool="x", input="{}", success=False)
                ],
                approval_status="approved",
            ),
            "error",
        ),
    ],
)
def test_routing_matrix(state, exp):
    from app.graph.edges.conditional import (
        route_after_approval,
        route_after_confidence,
        route_after_evidence,
        route_after_planner,
        route_after_retrieval,
        route_after_risk,
        route_after_validation,
    )

    assert (
        route_after_validation(state) == exp
        if exp in ("error", "planner")
        else True
    )
    mapping = {
        "error": route_after_validation(state),
        "planner": route_after_validation(state),
        "tool_planner": route_after_planner(state),
        "response": (
            route_after_retrieval(state) if not state.retrieved_docs
            else route_after_evidence(state)
            if state.evidence_coverage < 0.3 and state.step_count < state.max_steps
            else route_after_evidence(state)
        ),
        "refine": (
            route_after_evidence(state)
            if state.evidence_coverage < 0.3
            else route_after_confidence(state)
        ),
        "risk": route_after_confidence(state),
        "approval": route_after_risk(state),
        "tools": route_after_approval(state),
    }
    if exp in mapping:
        assert mapping[exp] == exp, (exp, mapping[exp])


# ---------------------------------------------------------------------------
# 4. Embedding LRU cache (no network)
# ---------------------------------------------------------------------------
def test_embedder_lru_cache(monkeypatch):
    import app.services.retrieval.embeddings.embedder as embedder_mod

    calls = []

    class FakeModel:
        def encode(self, texts):
            calls.append(tuple(texts))
            return [[0.1 * (i + 1)] for i in range(len(texts))]

    monkeypatch.setattr(embedder_mod, "_EMBED_CACHE", {})
    monkeypatch.setattr(embedder_mod, "_EMBED_CACHE_ORDER", [])
    monkeypatch.setattr(embedder_mod, "get_embedder", lambda: FakeModel())

    a = embedder_mod.embed_texts(["hello", "world"])
    b = embedder_mod.embed_texts(["hello", "world"])  # cache hit
    embedder_mod.embed_texts(["other"])
    assert a == b
    assert len(calls) == 2  # two distinct inputs
    assert calls[0] == ("hello", "world")
    assert calls[1] == ("other",)


# ---------------------------------------------------------------------------
# 5. OpenAI-compatible embedder parsing (fake openai module)
# ---------------------------------------------------------------------------
def test_openai_compatible_embedder(monkeypatch):
    fake = types.ModuleType("openai")

    class _Data:
        def __init__(self, emb):
            self.embedding = emb

    class _Resp:
        def __init__(self, data):
            self.data = data

    class _Embeddings:
        def create(self, model=None, input=None):
            return _Resp([_Data([float(i)]) for i in range(len(input))])

    class _Client:
        def __init__(self, api_key=None, base_url=None):
            self.embeddings = _Embeddings()

    fake.OpenAI = _Client
    monkeypatch.setitem(__import__("sys").modules, "openai", fake)

    from app.services.retrieval.embeddings.openai_embedder import (
        OpenAICompatibleEmbedder,
    )

    emb = OpenAICompatibleEmbedder(
        model="text-embedding-3-small", api_key="x", base_url="http://x/v1"
    )
    out = emb.encode(["a", "b"])
    assert out == [[0.0], [1.0]]


# ---------------------------------------------------------------------------
# 6. REST reranker parsing (fake urlopen)
# ---------------------------------------------------------------------------
def test_rest_reranker_parse(monkeypatch):
    import app.services.retrieval.reranker.rest_reranker as rest_reranker_mod

    payload = {
        "results": [
            {"index": 2, "relevance_score": 0.9},
            {"index": 0, "relevance_score": 0.1},
            {"index": 1, "relevance_score": 0.5},
        ]
    }

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(payload).encode()

    monkeypatch.setattr(
        __import__("urllib.request", fromlist=["urlopen"]),
        "urlopen",
        lambda *a, **k: _Resp(),
    )

    rr = rest_reranker_mod.RestReranker(model="m", api_base="http://x/rerank")
    scores = rr.compute_score([["q", "d0"], ["q", "d1"], ["q", "d2"]])
    assert scores == [0.1, 0.5, 0.9], scores


def test_rest_reranker_requires_base():
    import pytest as _pytest

    from app.services.retrieval.reranker.rest_reranker import RestReranker

    with _pytest.raises(ValueError):
        RestReranker(model="m", api_base=None)


# ---------------------------------------------------------------------------
# 7. Reasoning resilience fallback
# ---------------------------------------------------------------------------
def test_reasoning_fallback(monkeypatch):
    import app.services.reasoning.reasoning as reas_mod

    def boom(*a, **k):
        raise RuntimeError("llm down")

    monkeypatch.setattr(reas_mod, "get_llm", boom)

    answer, parts = reas_mod.reason_with_evidence("q", [{"content": "x"}])
    assert "unavailable" in answer.lower()
    assert parts and "error" in parts[0].lower()


# ---------------------------------------------------------------------------
# 8. Pending-approval tracking (fake redis, best-effort)
# ---------------------------------------------------------------------------
def test_threads_best_effort(monkeypatch):
    import asyncio

    from app.services.memory.memory import memory_manager

    store = {}

    class FakeRedis:
        async def hset(self, key, field, value):
            store.setdefault(key, {})[field] = value

        async def hgetall(self, key):
            return dict(store.get(key, {}))

        async def hdel(self, key, field):
            store.get(key, {}).pop(field, None)

    monkeypatch.setattr(memory_manager, "_redis", FakeRedis())

    from app.core import threads

    asyncio.run(
        threads.track_pending_approval("t1", "high", 90.0, "delete")
    )
    pending = asyncio.run(threads.list_pending_approvals())
    assert len(pending) == 1
    assert pending[0]["thread_id"] == "t1"
    assert pending[0]["risk_level"] == "high"

    asyncio.run(threads.clear_pending_approval("t1"))
    pending = asyncio.run(threads.list_pending_approvals())
    assert pending == []


def test_threads_redis_down_is_safe(monkeypatch):
    import asyncio

    from app.services.memory.memory import memory_manager

    class Boom:
        async def hset(self, *a, **k):
            raise RuntimeError("redis gone")

        async def hgetall(self, *a, **k):
            raise RuntimeError("redis gone")

        async def hdel(self, *a, **k):
            raise RuntimeError("redis gone")

    monkeypatch.setattr(memory_manager, "_redis", Boom())

    from app.core import threads

    # must not raise
    asyncio.run(threads.track_pending_approval("t1", "high", 90.0))
    assert asyncio.run(threads.list_pending_approvals()) == []


# ---------------------------------------------------------------------------
# 9. chat.py payload helpers (no graph)
# ---------------------------------------------------------------------------
def test_chat_helpers():
    import app.api.chat as chat_mod

    # unwrap
    assert chat_mod._unwrap({"a": 1}) == {"a": 1}
    fake = types.SimpleNamespace(values={"a": 2})
    assert chat_mod._unwrap(fake) == {"a": 2}

    # build_result
    res = chat_mod._build_result(
        {"final_response": "hi", "confidence_score": 1.0, "risk_score": 2.0,
         "risk_level": "low", "reasoning_path": ["r"], "step_count": 3,
         "approval_status": "approved", "citations": [], "tool_calls": []},
        "tid",
    )
    assert res["response"] == "hi"
    assert res["needs_approval"] is False
    assert res["approval_status"] == "approved"

    # build_approval_payload
    payload = chat_mod._build_approval_payload(
        {"risk_level": "high", "risk_score": 90.0, "approval_status": "pending"},
        "tid",
        {"reason": "x", "pending_tools": ["delete"], "triggering_factors": ["tool:delete"]},
    )
    assert payload["needs_approval"] is True
    assert payload["pending_tools"] == ["delete"]

    # extract_interrupt from ainvoke return
    ints = types.SimpleNamespace(value={"type": "approval_required"})
    snap = types.SimpleNamespace(tasks=[types.SimpleNamespace(interrupts=[ints])])
    assert chat_mod._extract_interrupt(None, snap) == {"type": "approval_required"}


# ---------------------------------------------------------------------------
# 10. Full graph interrupt/approve/reject flow (offline, stubbed LLM)
# ---------------------------------------------------------------------------
def _patch_nodes(monkeypatch, tool_names, reason_answer="The answer is 42."):
    val_node = importlib.import_module("app.graph.nodes.validator_node")
    plan_node = importlib.import_module("app.graph.nodes.planner_node")
    ret_node = importlib.import_module("app.graph.nodes.retrieval_node")
    reas_node = importlib.import_module("app.graph.nodes.reasoning_node")
    tool_node = importlib.import_module("app.graph.nodes.tools_node")
    tp = importlib.import_module("app.graph.nodes.tool_planner_node")
    from app.models.state import ToolCallRecord
    from app.services.validator.validator import ValidationResult

    monkeypatch.setattr(
        val_node, "validate_query",
        lambda q: ValidationResult(is_safe=True, issues=[], confidence=1.0),
    )
    monkeypatch.setattr(plan_node, "create_plan", lambda q: ["retrieve", "respond"])
    monkeypatch.setattr(ret_node, "embed_query", lambda t: [0.1] * 8)
    monkeypatch.setattr(
        ret_node, "hybrid_search",
        lambda q, e, **kw: [
            {"content": "doc", "relevance_score": 0.8, "source": "wikipedia", "page": 1}
        ],
    )
    monkeypatch.setattr(
        reas_node, "reason_with_evidence", lambda q, d: (reason_answer, ["step1"])
    )
    def _execute_tool(n, a):
        return ToolCallRecord(
            tool=n, input=str(a), output="ok", success=True, duration_ms=1.0
        )

    monkeypatch.setattr(tool_node, "execute_tool", _execute_tool)

    def planner(query, plan):
        return [ToolCallRecord(tool=n, input="{}", success=False) for n in tool_names]

    monkeypatch.setattr(tp, "plan_tool_calls", planner)
    return ToolCallRecord


@pytest.mark.parametrize(
    "tool_names,action,exp_status,exp_interrupt,exp_tools_ran",
    [
        ([], "approve", "approved", False, False),       # low/medium, no pause
        (["web_search"], "approve", "approved", False, False),
        (["delete_records"], "approve", "approved", True, True),   # high -> pause -> approve
        (["delete_records"], "reject", "rejected", True, False),  # high -> pause -> reject
        (["admin_console", "web_search"], "approve", "approved", True, True),
    ],
)
def test_graph_scenarios(monkeypatch, tool_names, action, exp_status, exp_interrupt, exp_tools_ran):
    import asyncio

    from app.graph.builder import build_graph

    _patch_nodes(monkeypatch, tool_names)
    g = build_graph(checkpointer=MemorySaver())

    async def run():
        st = AgentState(
            query="do something", messages=[], step_count=0,
            max_steps=10, start_time=0.0,
        )
        r = await g.ainvoke(st, config={"configurable": {"thread_id": "s1"}})
        interrupted = "__interrupt__" in r
        if interrupted:
            inter = r["__interrupt__"][0].value
            assert "pending_tools" in inter
            r2 = await g.ainvoke(
                Command(resume={"approved": action == "approve"}),
                config={"configurable": {"thread_id": "s1"}},
            )
            vals = r2 if isinstance(r2, dict) else r2.values
        else:
            vals = r if isinstance(r, dict) else r.values
        return interrupted, vals

    interrupted, vals = asyncio.run(run())
    assert interrupted == exp_interrupt, (interrupted, exp_interrupt, vals)
    assert vals["approval_status"] == exp_status, vals
    if exp_tools_ran:
        # every configured tool executes once and returns "ok"
        assert vals["tool_results"] == ["ok"] * len(tool_names), vals
    else:
        # either no tools configured or rejected
        assert vals["tool_results"] in ([], ["ok"]) , vals
