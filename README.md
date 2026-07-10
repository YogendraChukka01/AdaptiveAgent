# AdaptiveAgent

![CI](https://github.com/YogendraChukka01/AdaptiveAgent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Tests](https://img.shields.io/badge/tests-90%20passed-brightgreen)

**AdaptiveAgent** is a secure, explainable, and trustworthy **Agentic RAG** platform for building context-aware assistants on top of private knowledge bases. It pairs a LangGraph-orchestrated reasoning pipeline with a Next.js frontend and a Docker-based local stack.

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Development workflow](#development-workflow)
- [Testing](#testing)
- [Security](#security)
- [Recent fixes](#recent-fixes)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## Overview

AdaptiveAgent combines retrieval, reasoning, confidence scoring, risk checks, and human-in-the-loop approval in a single platform. It is designed for teams building internal copilots, knowledge assistants, and policy-aware AI experiences over private document collections.

Key design principles:

- **Safety first.** Every user query is screened for prompt injection (Sunglasses) and PII/SQL-injection patterns before it reaches the pipeline.
- **Grounded answers.** Responses are generated only from retrieved evidence; the system reports when coverage is insufficient instead of guessing.
- **Controlled execution.** Sensitive tools and high-risk plans require explicit human approval before anything runs.
- **Self-correcting retrieval.** When evidence or confidence is weak, the agent *refines* the query and widens retrieval rather than repeating the same failed search (CRAG / Self-RAG "repair" step).

---

## Features

- **Hybrid retrieval** -- dense vector (BGE-M3) + BM25 keyword + reranking (BGE reranker)
- **Evidence-grounded reasoning** with explicit reasoning traces and contradiction detection
- **Confidence scoring** -- 3-factor scoring (term coverage, doc count, credibility)
- **Risk assessment** -- 10-factor risk model with configurable thresholds
- **Approval gating** -- human-in-the-loop for high-risk tool execution
- **Self-correcting retry loop** -- rewrites/broadens queries on weak results (CRAG refine)
- **SSE streaming** -- real-time token-by-token responses via Server-Sent Events
- **Prompt injection detection** -- Sunglasses engine + regex-based SQL/PII detection
- **Audit logging** -- full audit trail in PostgreSQL with thread tracking
- **Thread isolation** -- every conversation uses a unique `thread_id` with PostgresSaver checkpointing
- **Docker Compose stack** for local development and orchestration

---

## Architecture

```
User -> Next.js -> FastAPI -> LangGraph -> ChromaDB / Ollama / PostgreSQL
```

**Backend** -- FastAPI + LangGraph + Ollama + ChromaDB (BGE-M3 embeddings, BM25, BGE reranker).

The agent is modelled as a stateful, cyclic LangGraph. The happy path:

```
step_counter -> validator -> planner -> tool_planner -> retrieval -> evidence ->
reasoning -> confidence -> risk -> approval -> tools -> response
```

**Self-correction.** If `evidence_coverage` or `confidence_score` is below its threshold (or a tool fails) and the `step_count` circuit breaker has not been reached, the graph routes to the `refine` node. `refine` rewrites/broadens the query (LLM with a deterministic fallback) and widens retrieval, so retries are productive and bounded by `max_steps`.

**Thread isolation.** Every request uses a unique `thread_id` with a PostgresSaver checkpointer, so conversations and approval pauses are isolated and resumable.

**Frontend** -- Next.js 15 + React 19 + TypeScript + Tailwind CSS 4.

**Infrastructure** -- Docker Compose for Postgres, Redis, Ollama, the backend, and the frontend.

---

## Project structure

```text
backend/
  app/
    api/              FastAPI routes (chat, upload, health, audit)
    core/             Config, database, dependencies, thread tracking
    graph/            LangGraph builder, 14 nodes, 8 conditional edges
    models/           Pydantic state schema and request/response schemas
    services/         LLM, retrieval, evidence, confidence, risk, tools, etc.
  tests/              90 tests (routing, scoring, nodes, integration)

frontend/
  src/
    app/              Next.js pages (main chat UI)
    components/       Chat input, message bubble, approval card, side panel
    lib/              API client (SSE streaming, upload, approval)

infra/                Docker Compose, Prometheus, Grafana
.github/              CI workflows, issue/PR templates
```

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- Git

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Frontend setup

```bash
cd ../frontend
npm install
```

### 4. Run the stack locally

```bash
cd ../infra
docker compose up -d --build
```

### 5. Access the app

- Frontend: http://localhost:3000
- API health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

---

## Configuration

Copy the example environment file before running the backend:

```bash
cp backend/.env.example backend/.env
```

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM backend (`ollama`, `openai`, `anthropic`, `groq`) |
| `LLM_MODEL` | `qwen2.5:7b` | Chat model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `EMBEDDING_PROVIDER` | `bge` | Embedding backend (`bge` or `openai`) |
| `RERANKER_PROVIDER` | `bge` | Reranker backend (`bge` or `rest`) |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_data` | Vector store path |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL checkpointer |
| `REDIS_URL` | `redis://localhost:6379/0` | Conversation memory + approval tracking |
| `AUTH_JWT_SECRET` | `change-me-in-production` | API auth secret (use `hmac.compare_digest`) |
| `MAX_STEPS` | `10` | Retry circuit-breaker bound |
| `EVIDENCE_THRESHOLD` | `0.3` | Min evidence coverage to skip refine |
| `CONFIDENCE_RETRY_THRESHOLD` | `30.0` | Min confidence to skip refine |
| `HIGH_RISK_THRESHOLD` | `70.0` | Risk score that triggers human approval |

See `backend/.env.example` for the full list.

---

## Development workflow

```bash
# Backend lint
cd backend && ruff check app tests

# Backend format
cd backend && ruff format app tests

# Backend tests (90 tests)
cd backend && python -m pytest -v

# Frontend lint
cd frontend && npm run lint

# Frontend typecheck
cd frontend && npm run typecheck

# Frontend build
cd frontend && npm run build
```

---

## Testing

The backend test suite (90 tests) covers:

- **Routing matrix** -- all conditional edge routing (validation, planner, retrieval, evidence, confidence, risk, approval, tools)
- **Tool routing** -- error handling, circuit breaker, refine on failure, success paths
- **Approval matrix** -- risk levels, tool counts, plan sizes vs auto-approve/pending
- **Scoring** -- confidence (3-factor), risk (10-factor), evidence (coverage, contradictions, credibility)
- **Retrieval** -- BM25, embedding cache, reranker parsing
- **Nodes** -- refine (LLM rewrite + deterministic fallback), reasoning fallback
- **Integration** -- graph execution, chat helpers, thread management

```bash
cd backend && python -m pytest -v
```

Embedding/reranker providers that require an external API are skipped automatically when the network is unavailable.

---

## Security

AdaptiveAgent implements multiple layers of defense:

| Layer | Mechanism |
|-------|-----------|
| **Input validation** | Query length limits, empty query detection |
| **Prompt injection** | Sunglasses engine + regex-based SQL injection/PII detection |
| **Output safety** | Hardcoded phrase blocklist on generated responses |
| **Auth** | Bearer token with `hmac.compare_digest` (timing-attack safe) |
| **Risk gating** | 10-factor risk model triggers human-in-the-loop approval |
| **Circuit breaker** | `max_steps` prevents infinite retry loops |
| **File upload** | 50MB size limit, allowed extension whitelist |
| **Tool sandboxing** | `read_file` restricted to allowed directories, 1MB read cap |
| **Thread isolation** | Each conversation uses a unique `thread_id` |

**Production checklist:**

- [ ] Change `AUTH_JWT_SECRET` from the default value
- [ ] Set `LLM_PROVIDER` and configure API keys
- [ ] Enable HTTPS (reverse proxy with nginx/caddy)
- [ ] Set `cors_origins` to your frontend domain
- [ ] Review `MAX_STEPS` and risk thresholds for your use case

---

## Recent fixes

### v2 (latest commit)

**35 bugs fixed** across backend and frontend:

- **SQL injection regex** -- `*/ *` never matched `/*` (star was regex quantifier)
- **Validator crash** -- SunglassesEngine failure now degrades gracefully instead of crashing requests
- **Safety message loss** -- validator's detailed safety error no longer overwritten by generic error_node
- **History role loss** -- conversation history now correctly maps assistant responses to `AIMessage`
- **Shared mutable dicts** -- `[{}]*N` metadata bug fixed (caused metadata corruption)
- **Reranker crash** -- single-document case now handles `float` vs `list` return
- **Upload DoS** -- 50MB file size limit prevents memory exhaustion
- **SSE crash** -- frontend JSON.parse on malformed SSE data now caught gracefully
- **Streaming errors** -- graph exceptions now emit error events instead of breaking the stream
- **Auth timing attack** -- replaced `!=` with `hmac.compare_digest`
- **Risk default** -- `risk_level` now defaults to `"low"` instead of `"high"`
- **Evidence threshold** -- response_node now uses configurable `evidence_min_coverage`
- **Redis leak** -- added `close()` method to MemoryManager
- **Tool file read** -- capped at 1MB to prevent OOM
- **Dead code removed** -- 7 unused state fields, 2 dead routing paths, unused frontend packages

See `git log` for the full diff.

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Support

If you run into issues or want to discuss improvements, open an issue or start a discussion on GitHub.
