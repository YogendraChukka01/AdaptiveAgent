# SafeAgent - Build Guide for AI Coding Agents

## Project Overview

A secure, explainable Agentic RAG platform using LangGraph + FastAPI + Ollama + ChromaDB.

## Critical Rules (DO NOT VIOLATE)

1. **State must use Pydantic `BaseModel`** - NOT TypedDict. Pydantic provides runtime validation.
2. **Only the `messages` field uses `Annotated[list, add_messages]`** - all other list fields use plain `list[...]` (last-write-wins). `add_messages` *appends*, so applying it to `plan`/`retrieved_docs`/etc. would accumulate values across the retry loop and cause bugs.
3. **Never mutate state directly** - Always return partial dict from nodes.
4. **Every LangGraph node must return dict** - Keys match state field names.
5. **Thread isolation required** - Every request needs unique `thread_id`.
6. **PostgresSaver for production** - Never use `MemorySaver` in deployment.
7. **Circuit breaker on step_count** - `max_steps` hard limit prevents infinite loops.
8. **Ollama model must support tool calling** - Only `qwen2.5:7b`, `llama3.1:8b`, `mistral:7b`.
9. **ChromaDB queries must include `include=["documents","metadatas","distances"]`**.
10. **BGE models must use `use_fp16=True`** to avoid OOM.
11. **Retry loops must REFINE, not repeat** - When evidence_coverage/confidence is low (or a tool fails), route to `refine` (not back to validation/planning). `refine` rewrites/broadens the query (LLM with deterministic fallback) and widens retrieval `k`; it must keep incrementing `step_count` so the `max_steps` circuit breaker still holds. This implements the CRAG/Self-RAG "repair" step.

## Architecture

```
User → Next.js → FastAPI → LangGraph (validator→planner→tool_planner→retrieval→evidence→reasoning→confidence→risk→approval→tools→response) → ChromaDB/BG
Retry loop: evidence/confidence/tool-failure → refine → retrieval (rewrites query + widens k, bounded by max_steps)
```

## File Map

| Path | Purpose |
|---|---|
| `backend/app/models/state.py` | AgentState Pydantic schema |
| `backend/app/graph/builder.py` | LangGraph StateGraph compilation |
| `backend/app/graph/nodes/*.py` | One file per graph node |
| `backend/app/graph/edges/conditional.py` | All conditional routing |
| `backend/app/services/validator/validator.py` | Prompt injection (Sunglasses) |
| `backend/app/services/retrieval/` | BGE-M3 + BM25 + reranker + ChromaDB |
| `backend/app/services/confidence/confidence.py` | 3-factor scoring |
| `backend/app/services/risk/risk.py` | 10-factor risk model |
| `backend/app/api/chat.py` | SSE streaming endpoint |
| `infra/docker-compose.yml` | PG + Redis + Ollama + Backend + Frontend |

## Testing
```bash
cd backend && python -m pytest tests/ -v
```

## Run
```bash
docker compose -f infra/docker-compose.yml up -d
```
