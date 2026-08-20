# AdaptiveAgent — Remediation Change Log

**Date:** 2026-08-06
**Scope:** Backend (`backend/app`), Frontend (`frontend/src`), Tests (`backend/tests`)
**Basis:** "Complete Bug Fix & Production Hardening PRD" v1.0
**Status:** Remediation pass 1 applied. Verification and remaining tasks below.

This document records **exactly what was changed**, the **reason** for each change, and the **next steps** that remain. It is the local audit log; the code changes described here are the ones pushed to GitHub.

---

## 1. Critical Runtime Bugs Fixed (highest severity)

### 1.1 `backend/app/graph/nodes/tools_node.py` — tools never executed (coroutine never awaited)

- **Before:** `tools_node` was a **sync** function that called `execute_tool(...)` without `await`. Since `execute_tool` is `async def` (`tool_registry.py:61`), every call returned an un-awaited coroutine — tools silently never ran — and `[r.output or "" for r in executed]` would crash with `AttributeError: 'coroutine' object has no attribute 'output'`.
- **After:** node is `async def` and awaits `execute_tool(...)`. `from typing import Any` added.
- **Reason:** real runtime bug — tool execution and post-processing would crash or no-op at runtime.

### 1.2 `backend/app/core/deps.py` — startup crash (`AsyncPostgresSaver(pool=...)`)

- **Before:** `AsyncPostgresSaver(pool=_pool, serde=serde)` → `TypeError: __init__() got an unexpected keyword argument 'pool'`. Verified against installed source: `def __init__(self, conn, pipe=None, serde=None)`.
- **After:** pool passed positionally: `AsyncPostgresSaver(_pool, serde=serde)`.
- **Reason:** guaranteed `TypeError` on app startup when the graph initialises.

### 1.3 `backend/app/api/chat.py::_unwrap` — bound-method returned instead of state dict

- **Before:** for a non-dict result the helper returned `result.values` (the bound method), so downstream `.get(...)` calls crashed.
- **After:** uses `model_dump()` for pydantic models, returns `{}` otherwise.
- **Reason:** latent crash on any non-dict graph result.

### 1.4 `backend/app/graph/nodes/planner_node.py` — invalid state key `planner_output`

- **Before:** the retry-exceeded path returned `{"error": ..., "planner_output": ...}` — `planner_output` is not a field of `AgentState` and would be rejected/dropped by the state schema.
- **After:** returns only `{"error": ...}`; signature `-> dict[str, Any]`.
- **Reason:** dead/invalid key (grep confirmed a single reference); removing it avoids state-schema errors.

---

## 2. Crash-class Fix — LLM content normalisation (`str | list[...]`)

**New helper:** `backend/app/core/text.py`

- Adds `content_to_str(content: Any) -> str` which normalises LangChain `BaseMessage.content` — typed `str | list[str | dict[Any, Any]]` — into a plain `str` (handles str, list of `{"type": "text", "text": ...}` blocks, `None`, else `str()`).
- **Reason:** `.strip()`, `.split()`, `json.loads` crash when content is a list of blocks. Applied at all 7 call sites that parse LLM output:

| File | Change |
|---|---|
| `services/planner/planner.py` | `json.loads(content_to_str(response.content).strip())` |
| `services/judge/__init__.py` | normalisation at 4 call sites; removed 6 now-unneeded `# type: ignore[union-attr]` |
| `services/reasoning/reasoning.py` | `content = content_to_str(response.content)` |
| `services/memory/memory_worker.py` | `content_to_str(response.content).strip()` + list-isinstance guards |
| `graph/nodes/refine_node.py` | `content_to_str(llm.invoke(...).content).strip()` |
| `graph/nodes/tool_planner_node.py` | `json.loads(content_to_str(response.content).strip())` |
| `graph/nodes/validator_node.py` | `content_to_str(state.messages[-1].content)` |

---

## 3. Type-safety / mypy fixes (mechanical, no behaviour change)

All `-> dict` returns annotated as `-> dict[str, Any]`, bare `list`/`dict` params given type args, untyped helpers annotated. Files touched:

- **Graph nodes (all 15 + error):** `step_counter.py`, `validator_node.py`, `planner_node.py`, `tool_planner_node.py`, `retrieval_node.py`, `evidence_node.py`, `reasoning_node.py`, `confidence_node.py`, `risk_node.py`, `approval_node.py`, `tools_node.py`, `refine_node.py`, `response_node.py`, `eval_node.py`, `error_node.py`
- **Graph:** `builder.py` — added `CompiledGraph = CompiledStateGraph[AgentState, Any, Any, Any]` type alias (see §4)
- **API:** `chat.py`, `audit.py`, `upload.py`, `health.py`, `evaluate.py`
- **Services:** `memory.py`, `memory_worker.py`, `validator.py`, `confidence.py`, `evidence.py`, `hybrid_search.py`, `risk.py`, `llm.py`, `judge/__init__.py`, `eval/__init__.py`, `planner.py`, `reasoning.py`
- **Retrieval:** `embeddings/embedder.py`, `reranker.py`, `vector_store/base.py`, `chroma_store.py`, `qdrant_store.py`, `pinecone_store.py`, `pgvector_store.py`
- **Models:** `schemas.py`
- **Core:** `deps.py`, `threads.py`, `main.py`

### Key fixes

| File | Fix |
|---|---|
| `services/retrieval/embeddings/embedder.py` | `_EMBED_CACHE: OrderedDict[tuple[str, ...], list[list[float]]]` (was `list[float]`); `get_embedder() -> Any` (was `-> object`, breaking `.encode()`) |
| `services/llm.py` | `cast(BaseChatModel, ChatOpenAI(...))` for openai/anthropic/google/groq; `from litellm import Router  # type: ignore[attr-defined]` |
| `services/eval/__init__.py` | `_Wrapper.embed_documents/embed_query` correctly typed with `hasattr(tolist)` guards |
| `services/retrieval/vector_store/chroma_store.py` | full type pass: `metadatas: list[dict[str, Any]] | None`, isinstance guards on client/query/count, `-> Any` for clients |
| `services/retrieval/vector_store/qdrant_store.py` / `pinecone_store.py` | same pattern; pinecone `vector_count` coerced via `int(...)` |
| `services/retrieval/vector_store/pgvector_store.py` | full type pass; async/sync override mismatch documented + suppressed (see §4) |
| `services/validator/validator.py` | `PII_PATTERNS: list[re.Pattern[str]]`, `SQL_INJECTION_PATTERNS: list[re.Pattern[str]]`, `_get_engine() -> Any` |
| `core/threads.py` | `_redis() -> Any` (Redis client is untyped in stubs) |
| `graph/builder.py` + `api/chat.py` + `core/deps.py` | `CompiledGraph` alias replaces bare `CompiledStateGraph` |
| `api/chat.py` | `history_messages: list[BaseMessage]` annotation |

### `pgvector_store.py` — async/sync override mismatch (suppressed, not silently changed)

`BaseVectorStore` declares sync `add_documents`/`query_similar`; `PGVectorStore` overrides them as `async` (asyncpg is inherently async). Nothing in the app routes through PGVector today (the live path uses `chroma_store` module functions). Rather than rewrite working opt-in code, the divergence is marked `# type: ignore[override]` with an explanatory class docstring. **Flagged for follow-up** (see §6).

---

## 4. About the `.d`-style type declaration files you asked about

No `.d` file was created by these edits. Two things may be confused here:

1. **`CompiledGraph` alias (in `backend/app/graph/builder.py`)** — this is the closest thing: a Python type **alias** that gives a concrete name to the generic `CompiledStateGraph[AgentState, Any, Any, Any]`. It is a runtime value used by mypy only; it is **not** a declaration file, and it was created because LangGraph's `CompiledStateGraph` is generic over four parameters, so bare `CompiledStateGraph` produces a mypy `type-arg` error in `builder.py`, `deps.py`, and `chat.py`.

2. **Frontend `.d.ts` files that already exist** — `frontend/next-env.d.ts` (auto-generated by Next.js for TS ambient types; not created by these edits) and `frontend/tsconfig.tsbuildinfo` (a tsc build cache, not a source file). Neither was created or modified by this remediation.

If you are referring to a different `.d` file you saw, tell me the path and I'll explain what it is.

---

## 5. Tests updated

- `backend/tests/test_upgrades.py` — the `_execute_tool` monkeypatch was changed from a sync function to `async def _execute_tool(n, a)` to match the now-async `tools_node`. Test invokes the graph via `g.ainvoke`, so this keeps it consistent.
- **Test suite status:** 87 passed / 7 failed at last full run. All 7 failures are **environment-only** on this Windows box (psycopg cannot import without libpq for `test_chat_helpers` + 5 `test_graph_scenarios`; `test_embedder_lru_cache` — ModuleNotFoundError). They pass in CI (`python:3.12-slim` with libpq installed).

---

## 6. Next Steps (remaining / not yet done)

> Editing stopped on request. These are documented, **not** applied.
> **Detailed ordered work list:** [`docs/NEXT_STEPS.md`](./NEXT_STEPS.md) — Step 1 (mypy), Step 2 (frontend), Step 3 (security), Step 4 (infra), Step 5 (docs), Step 6 (final verification), with exact file:line fixes and commit grouping.

### 6.1 Remaining mypy errors (fresh run, 2026-08-06: **18 errors**; down from 191 baseline)

| File:line | Error | Fix |
|---|---|---|
| `app/models/state.py:36` | `retrieved_docs: list[dict]` — missing `dict` type args | `list[dict[str, Any]]` |
| `app/services/memory/memory.py:14` | `MemoryManager.__init__` missing return annotation | `-> None` |
| `app/services/memory/memory.py:73` | `memory_manager = MemoryManager()` — call to untyped function | resolved once `__init__` annotated |
| `app/services/reasoning/reasoning.py:11` | missing `dict` type args | `dict[str, Any]` |
| `app/services/memory/memory_worker.py:180` | helper missing return annotation | `-> None` |
| `app/services/judge/__init__.py:83` | `Returning Any from function declared to return list[Any]` | wrap in explicit `list(...)` |
| `app/graph/nodes/refine_node.py:45` | missing `dict` type args | `dict[str, Any]` |
| `app/core/deps.py:51` | `AsyncPostgresSaver` arg type: `AsyncConnectionPool[AsyncConnection[tuple[...]]]` vs expected `...dict[str, Any]` | annotate pool generic arg (cosmetic; runtime correct) |
| `app/api/chat.py:141, 284, 361` | `astream_events` / `ainvoke` overload mismatch (`config` typed as `dict[str, Any]`, LangGraph expects `RunnableConfig`) | type `config` as `RunnableConfig` |
| `app/api/chat.py:175, 286, 303, 372` | `aget_state(config)` — `config` should be `RunnableConfig` not `dict` | same fix |

> **Note:** all 18 are type-only. None change runtime behaviour. The `deps.py:51` and `chat.py` LangGraph-typing errors stem from LangGraph's own stubs expecting `RunnableConfig`/`AsyncConnection[dict[str, Any]]`; the values passed are correct at runtime.

### 6.2 Frontend

- **`src/app/page.tsx:122`** — `handleSend` uses `lastResult` inside the callback but omits it from the dependency array (react-hooks/exhaustive-deps warning). Fix: add `lastResult` to deps or move the check to a ref.
- **`src/lib/api.ts`** — `streamChat`/`uploadDocument`/`approveAction` do **not** send the `X-API-Key` header the backend `require_api_key` dependency expects → frontend calls would return 401. Add the header from an env-configurable key.

### 6.3 Security pass (Task 4) — not yet run

docker-compose default credentials, `config.py` `database_url` defaults, `.env.example` JWT placeholder, unpinned Docker images, simulated `web_search` tool, `SECURITY.md` placeholder email, prometheus config → nonexistent `/metrics` endpoint.

### 6.4 Infra + CI/CD pass (Task 5)

Pin image versions; wire a real `/metrics` endpoint.

### 6.5 Testing + docs (Task 6)

README says "14 nodes"; graph now has 15 nodes (+ `error`). Update.

### 6.6 Final verification (Task 7)

Full `ruff`, `mypy`, `ruff format --check`, frontend `tsc --noEmit` + lint, full pytest; record final metrics.

---

## 6A. Verification status at push time

- **Backend mypy:** 18 errors remaining (fresh run) — all type-only, listed in §6.1.
- **Frontend `tsc --noEmit`:** ✅ passes (exit 0).
- **Frontend `next lint`:** 1 warning — `page.tsx:122` missing `lastResult` dep (see §6.2).
- **Backend pytest:** 87 passed / 7 failed — the 7 failures are environment-only (psycopg/libpq unavailable on this Windows box); they pass in CI. Full re-run pending for final verification.

---

## 7. Files changed in this push

**45 modified + 1 added** (see `git status` / `git diff` for the exact hunks):

- Modified: all files listed in §3 + `tests/test_upgrades.py`
- **Added:** `backend/app/core/text.py` (new `content_to_str` helper)
- **Added (this doc):** `docs/REMEDIATION_CHANGELOG.md`
