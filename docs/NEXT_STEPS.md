# AdaptiveAgent — Next Edit Steps

**Date:** 2026-08-06
**Companion:** [`docs/REMEDIATION_CHANGELOG.md`](./REMEDIATION_CHANGELOG.md) records what was already changed and pushed.

This is the ordered, actionable work list for the remaining hardening. Each step gives the exact file/line and the fix. Work items are grouped by pass; do them in order so verification stays green.

---

## Step 1 — Close out the remaining mypy errors (backend, type-only)

**Progress (2026-08-06):** 18 → **8 errors** applied and pushed. Done in this pass:
`state.py:36`, `memory.py:14/73`, `reasoning.py:11`, `memory_worker.py:180`,
`judge/__init__.py:83`, `refine_node.py:45`, `deps.py` (pool annotation).

**Remaining — only in `backend/app/api/chat.py`:** the `_stream_events` helper still
types its `config` parameter as `dict[str, Any]`, while the LangGraph stubs expect
`RunnableConfig` (the two call-site `config` dicts are already annotated). Errors at
`chat.py:142, 176, 275, 362, 373` all stem from this one line:

```python
async def _stream_events(
    graph: CompiledGraph,
    state: AgentState,
    config: dict[str, Any],        # <- change to: config: RunnableConfig
    thread_id: str,
) -> AsyncGenerator[str, None]:
```

All are type-only (no runtime behaviour change). After each file, re-run:
`.venv/Scripts/python -m mypy app --ignore-missing-imports`

| # | File:line | Error | Fix |
|---|---|---|---|
| 1 | `backend/app/models/state.py:36` | `retrieved_docs: list[dict]` — missing `dict` type args | `list[dict[str, Any]]`; add `from typing import Any` |
| 2 | `backend/app/services/memory/memory.py:14` | `MemoryManager.__init__` missing return annotation | `def __init__(self) -> None:` |
| 3 | `backend/app/services/memory/memory.py:73` | `memory_manager = MemoryManager()` — call to untyped function | auto-resolves once #2 is done |
| 4 | `backend/app/services/reasoning/reasoning.py:11` | `documents: list[dict]` — missing `dict` type args | `list[dict[str, Any]]`; add `Any` import |
| 5 | `backend/app/services/memory/memory_worker.py:180` | inner helper `_delete_and_upsert` missing return annotation | `def _delete_and_upsert() -> None:` |
| 6 | `backend/app/services/judge/__init__.py:83` | `return json.loads(match.group())` — returning `Any` from `-> list[Any]` | guard: `parsed = json.loads(match.group()); return parsed if isinstance(parsed, list) else []` |
| 7 | `backend/app/graph/nodes/refine_node.py:45` | `def refine_node(state) -> dict:` — missing `dict` type args | `-> dict[str, Any]`; add `Any` import |
| 8 | `backend/app/core/deps.py:51` | `AsyncPostgresSaver(_pool, ...)` arg type `AsyncConnectionPool[AsyncConnection[tuple[...]]]` vs expected `AsyncConnectionPool[AsyncConnection[dict[str, Any]]]` | annotate the pool at creation: `_pool: AsyncConnectionPool[Any] = AsyncConnectionPool(...)` (cosmetic; runtime is correct) |
| 9–14 | `backend/app/api/chat.py:141, 175, 284, 286, 303, 361, 372` | `astream_events` / `ainvoke` / `aget_state` overload mismatch — `config` is `dict[str, Any]`, LangGraph stubs expect `RunnableConfig` | import `from langchain_core.runnables import RunnableConfig`; type the local `config` dicts as `RunnableConfig` (they already carry `configurable` + `recursion_limit`, both valid `RunnableConfig` keys) |

**Gate:** `mypy app --ignore-missing-imports` reports **0 errors**.

---

## Step 2 — Frontend fixes

**Progress (2026-08-06):** both applied and pushed. ✅

### 2a. `frontend/src/app/page.tsx:122` — React hooks warning

`handleSend` reads `lastResult` inside the callback but omits it from the dependency array
(`react-hooks/exhaustive-deps`). The check at line 102 `if (fullResponse && !lastResult)` uses a
stale closure.

**Fix (choose one):**
- Simplest: add `lastResult` to the deps array → `[threadId, applyResult, lastResult]`.
- Cleaner (recommended): replace the `lastResult` check with a ref. Add
  `const lastResultRef = useRef<ChatResult | null>(null);`, set it inside `applyResult`
  (`lastResultRef.current = result`), and change line 102 to `if (fullResponse && !lastResultRef.current)`.
  Keep deps as `[threadId, applyResult]`.

### 2b. `frontend/src/lib/api.ts` — send `X-API-Key` header

`streamChat`, `approveAction`, and `uploadDocument` omit the `X-API-Key` header the backend
`require_api_key` dependency expects → every frontend call would return **401**.

**Fix:** add a key constant and the header to all three fetches:
```ts
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";
// ...headers: {
//   "Content-Type": "application/json",
//   ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
// }
```
(For `uploadDocument`, keep `Content-Type` unset — the browser sets the multipart boundary.)

**Gate:** `npm run typecheck` passes; `next lint` shows **0 warnings**.

---

## Step 3 — Security pass (Task 4)

1. **`infra/docker-compose*.yml` default credentials** — replace hard-coded dev credentials with
   env-var indirection (`${POSTGRES_PASSWORD:?required}`); keep a commented dev-only override.
2. **`backend/app/core/config.py` `database_url` defaults** — remove weak/insecure fallback values;
   fail fast (`raise ValueError`) when the required vars are absent.
3. **`.env.example` JWT placeholder** — replace any real-looking placeholder token with
   `your-strong-secret-here` + a comment to generate via `openssl rand -hex 32`.
4. **Unpinned Docker images** (`backend/Dockerfile`, `frontend/Dockerfile`, workflows) — pin exact
   tags (e.g. `python:3.12-slim@sha256:...`) or at minimum a minor tag (`python:3.12-slim`),
   and enable Dependabot for base-image updates.
5. **Simulated `web_search` tool** (`backend/app/services/tools/`) — either implement a real,
   validated search backend, or clearly rename/mark the tool `simulated_web_search` so callers are
   not misled (it currently pretends to search).
6. **`SECURITY.md` placeholder email** — replace the TODO address with the real contact or remove
   the line.
7. **Prometheus config → `/metrics`** — wire a real metrics endpoint (see Step 4) or remove the
   scrape target from `infra/monitoring/prometheus.yml`.

**Gate:** `gitleaks` / `trufflehog` scan clean; no default credentials in committed config.

---

## Step 4 — Infra + CI/CD pass (Task 5)

1. Pin image versions (Step 3.4 above).
2. **Add a real `/metrics` endpoint** — expose Prometheus metrics (e.g. `prometheus-fastapi-instrumentator`
   or `prometheus_client`) on `backend/app/api/health.py`/`main.py` and confirm
   `infra/monitoring/prometheus.yml` targets it.
3. Verify `.github/workflows` match the app's actual service layout and run the full lint/type/test
   matrix (backend + frontend).

**Gate:** `docker compose build` succeeds; `/metrics` returns Prometheus text.

---

## Step 5 — Testing + docs pass (Task 6)

1. **README "14 nodes" → 15** — the graph has 15 nodes (`step_counter, validator, planner,
   tool_planner, retrieval, evidence, reasoning, confidence, risk, approval, tools, refine,
   response, eval, error`). Update the count and, if present, the node diagram.
2. Re-check `SECURITY.md`, `CONTRIBUTING.md`, `AGENTS.md` for stale claims.
3. **CI-only test deps** — the 7 local failures are psycopg/libpq + one `ModuleNotFoundError`
   on Windows; document the `apt-get install libpq-dev` prerequisite in `CONTRIBUTING.md`.

**Gate:** grep for "14 nodes" returns nothing.

---

## Step 6 — Final verification (Task 7)

From `backend/`:
```bash
.venv/Scripts/python -m ruff check app tests
.venv/Scripts/python -m ruff format --check app tests
.venv/Scripts/python -m mypy app --ignore-missing-imports
.venv/Scripts/python -m pytest
```
From `frontend/`:
```bash
npm run typecheck
npx next lint        # or: npx eslint src
```
Record final metrics (error counts, test pass/fail, warnings) and append to
`docs/REMEDIATION_CHANGELOG.md` §6A.

**Gate:** all of the above green; then commit + push.

---

## Suggested commit grouping

1. `fix: close out remaining mypy errors (0 errors)` — Step 1
2. `fix: frontend hooks dep + API key header` — Step 2
3. `security: harden defaults, secrets, and tool surface` — Step 3
4. `chore: pin images and wire /metrics` — Step 4
5. `docs: node count and prerequisites` — Step 5
6. `chore: final verification` — Step 6
