# AdaptiveAgent

![CI](https://github.com/YogendraChukka01/AdaptiveAgent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Tests](https://img.shields.io/badge/tests-94%20passed-brightgreen)

**AdaptiveAgent** is a production-grade, secure, and explainable **Agentic RAG** platform for building context-aware assistants on private knowledge bases. It combines a LangGraph-orchestrated reasoning pipeline with a Next.js frontend, multi-vector store support, LLM-as-judge evaluation, and automatic cloud fallback — all in a Docker-based local stack.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Vector Store Backends](#vector-store-backends)
- [Cloud Fallback](#cloud-fallback)
- [Evaluation Framework](#evaluation-framework)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [API Reference](#api-reference)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AdaptiveAgent combines retrieval, reasoning, confidence scoring, risk assessment, and human-in-the-loop approval into a single, auditable platform. It is designed for teams building internal copilots, knowledge assistants, and policy-aware AI experiences over private document collections.

**Design principles:**

- **Safety first.** Every query is screened for prompt injection (Sunglasses), SQL injection, and PII before it reaches the pipeline.
- **Grounded answers.** Responses are generated only from retrieved evidence; the system reports when coverage is insufficient instead of hallucinating.
- **Controlled execution.** Sensitive tools and high-risk plans require explicit human approval before execution.
- **Self-correcting retrieval.** When evidence or confidence is weak, the agent rewrites and broadens the query (CRAG/Self-RAG repair step) rather than repeating the same failed search.
- **Observable.** Full audit trails, LangSmith tracing, and Ragas evaluation metrics out of the box.

---

## Key Features

### Core RAG Pipeline
- **Hybrid retrieval** — dense vector (BGE-M3) + BM25 keyword search + BGE reranker
- **Evidence-grounded reasoning** with explicit reasoning traces and contradiction detection
- **Confidence scoring** — 3-factor model (term coverage, document count, credibility)
- **Risk assessment** — 10-factor risk model with configurable thresholds
- **Approval gating** — human-in-the-loop for high-risk tool execution via interrupt/resume
- **Self-correcting retry loop** — rewrites/broadens queries on weak results (CRAG refine)
- **Post-generation evaluation** — LLM-as-judge scores faithfulness and relevancy before delivery

### Multi-Vector Store Support
- **ChromaDB** (default) — local embedded, zero-config
- **PGVector** — production PostgreSQL with pgvector extension
- **Qdrant** — high-performance vector search with pre-filtering
- **Pinecone** — managed cloud vector database
- Store-agnostic abstraction layer — switch backends via a single config variable

### Cloud Fallback
- **LiteLLM Router** — automatic fallback from local Ollama to cloud models (GPT-4o-mini, Claude, etc.)
- Handles timeouts, VRAM exhaustion, rate limits, and connection failures transparently
- Per-deployment retry policies and cooldown on degraded backends

### Evaluation Framework
- **Ragas integration** — faithfulness, answer relevancy, context precision, context recall
- **Claim extraction** — Ragas-style NLI verification of individual claims
- **Heuristic baseline** — fast, zero-cost scoring when LLM judge is unavailable
- `POST /evaluate` API endpoint for continuous evaluation

### Production Infrastructure
- **SSE streaming** — real-time token-by-token responses via Server-Sent Events
- **Prompt injection detection** — Sunglasses engine + structural SQL injection patterns
- **Audit logging** — full audit trail in PostgreSQL with thread tracking
- **API key auth** — `X-API-Key` header with timing-attack-safe comparison
- **GitHub Actions CI/CD** — lint, format, test, type-check on every push
- **Docker Compose stack** — Postgres, Redis, Ollama, backend, frontend

---

## Architecture

```
                          ┌─────────────────────────────────────┐
                          │           Frontend (Next.js)        │
                          │   React 19 · TypeScript · Tailwind  │
                          └──────────────┬──────────────────────┘
                                         │ SSE / REST
                          ┌──────────────▼──────────────────────┐
                          │          Backend (FastAPI)           │
                          │   API Key Auth · Rate Limiting       │
                          └──────────────┬──────────────────────┘
                                         │
                 ┌───────────────────────▼───────────────────────┐
                 │              LangGraph Pipeline                │
                 │                                               │
                 │  step_counter → validator → planner →         │
                 │  tool_planner → retrieval → evidence →        │
                 │  reasoning → confidence → risk → approval →   │
                 │  tools → response → eval → [refine | END]    │
                 │                                               │
                 └──┬──────────┬──────────┬──────────┬──────────┘
                    │          │          │          │
            ┌───────▼──┐ ┌────▼────┐ ┌───▼───┐ ┌───▼────────┐
            │ Ollama /  │ │ Vector  │ │ Redis │ │ PostgreSQL │
            │ LiteLLM   │ │ Store   │ │       │ │            │
            │ Router    │ │ (multi) │ │       │ │            │
            └───────────┘ └─────────┘ └───────┘ └────────────┘
```

### Backend

FastAPI + LangGraph + Ollama/LiteLLM + configurable vector store (ChromaDB/PGVector/Qdrant/Pinecone).

The agent is modeled as a **stateful, cyclic LangGraph** with 14 nodes and 8 conditional edges:

```
step_counter → validator → planner → tool_planner → retrieval → evidence →
reasoning → confidence → risk → approval → tools → response → eval
```

**Self-correction:** If `evidence_coverage` or `confidence_score` is below threshold (or a tool fails) and the `step_count` circuit breaker has not been reached, the graph routes to the `refine` node. `refine` rewrites/broadens the query and widens retrieval.

**Post-generation eval:** After response generation, the `eval` node scores faithfulness (Ragas-style claim extraction + NLI) and answer relevancy. If the score is below `eval_threshold`, the graph loops back to `refine` for another attempt.

**Cloud fallback:** When `LLM_FALLBACK_MODEL` is configured, LiteLLM Router transparently falls back from local Ollama to a cloud model on timeout, connection error, or VRAM exhaustion.

### Frontend

Next.js 15 + React 19 + TypeScript + Tailwind CSS 4.

- Real-time SSE streaming with token-by-token display
- Human-in-the-loop approval cards
- Side panel with confidence, risk, and eval scores
- Dark mode support

### Infrastructure

Docker Compose for PostgreSQL, Redis, Ollama, backend, and frontend.

---

## Project Structure

```text
backend/
  app/
    api/                  FastAPI routes (chat, upload, health, audit, evaluate)
    core/                 Config, auth, database, dependencies, thread tracking
    graph/
      builder.py          LangGraph StateGraph compilation (14 nodes)
      edges/              8 conditional routing functions
      nodes/              One file per graph node
    models/               Pydantic state schema, request/response schemas
    services/
      judge/              LLM-as-judge faithfulness scoring (Ragas-style)
      eval/               Ragas evaluation framework integration
      retrieval/
        vector_store/     Multi-backend abstraction (Chroma, PGVector, Qdrant, Pinecone)
        embeddings/       BGE-M3 + OpenAI-compatible embedders
        reranker/         BGE reranker + REST API reranker
      llm.py              LiteLLM Router with cloud fallback
      confidence/         3-factor confidence scoring
      evidence/           Evidence verification + contradiction detection
      risk/               10-factor risk assessment
      validator/          Prompt injection + SQL injection + PII detection
      reasoning/          Chain-of-thought reasoning with LLM
      tools/              Tool registry + execution sandbox
      memory/             Redis conversation store + background distillation
      audit/              PostgreSQL audit logging
  tests/                  94 tests (routing, scoring, nodes, integration, eval)

frontend/
  src/
    app/                  Next.js pages (main chat UI, error boundary)
    components/           Chat input, message bubble, approval card, side panel
    lib/                  API client (SSE streaming, upload, approval)

infra/                    Docker Compose, Prometheus, Grafana
.github/                  CI workflows (backend + frontend)
```

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- Git

---

## Quick Start

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

### 4. Configure environment

```bash
cd ../backend
cp .env.example .env   # edit with your settings
```

### 5. Run the stack

```bash
cd ../infra
docker compose up -d --build
```

### 6. Access the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Evaluation | POST http://localhost:8000/evaluate |

---

## Configuration

All settings are configured via environment variables or `.env` file. See `backend/app/core/config.py` for the full schema.

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama`, `openai`, `anthropic`, `google`, `groq` |
| `LLM_MODEL` | `qwen2.5:7b` | Chat model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `EMBEDDING_PROVIDER` | `bge` | Embedding backend: `bge` or `openai` |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Embedding model |
| `RERANKER_PROVIDER` | `bge` | Reranker backend: `bge` or `rest` |

### Vector Store

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_STORE_TYPE` | `chroma` | Backend: `chroma`, `pgvector`, `qdrant`, `pinecone` |
| `VECTOR_STORE_COLLECTION` | `safeagent_docs` | Collection/index name |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_data` | ChromaDB data path |
| `PGVECTOR_CONNECTION_STRING` | — | PostgreSQL connection string (pgvector) |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `PINECONE_API_KEY` | — | Pinecone API key |
| `PINECONE_INDEX_NAME` | — | Pinecone index name |

### Cloud Fallback

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_FALLBACK_MODEL` | — | Cloud fallback model (e.g. `gpt-4o-mini`) |
| `LLM_FALLBACK_API_KEY` | — | API key for fallback provider |
| `LLM_FALLBACK_PROVIDER` | — | Fallback provider (default: `openai`) |
| `LLM_REQUEST_TIMEOUT` | `60` | Primary model timeout (seconds) |

### Evaluation

| Variable | Default | Description |
|----------|---------|-------------|
| `EVAL_ENABLED` | `true` | Enable post-generation evaluation |
| `EVAL_THRESHOLD` | `0.85` | Min score to accept response |
| `EVAL_JUDGE_MODEL` | — | LLM model for evaluation judge |
| `EVAL_RAGAS_ENABLED` | `true` | Enable Ragas claim extraction |
| `EVAL_RELEVANCY_ENABLED` | `true` | Enable answer relevancy scoring |

### Pipeline Tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_STEPS` | `10` | Retry circuit-breaker bound |
| `EVIDENCE_THRESHOLD` | `0.3` | Min evidence coverage to skip refine |
| `EVIDENCE_MIN_COVERAGE` | `0.5` | Min coverage for response generation |
| `CONFIDENCE_RETRY_THRESHOLD` | `30.0` | Min confidence (0-100) to skip refine |
| `HIGH_RISK_THRESHOLD` | `70.0` | Risk score triggering human approval |
| `API_KEY` | `""` | API key for auth (empty = dev mode) |

---

## Vector Store Backends

Switch between vector stores by setting `VECTOR_STORE_TYPE`:

```bash
# ChromaDB (default, local embedded)
VECTOR_STORE_TYPE=chroma

# PGVector (production PostgreSQL)
VECTOR_STORE_TYPE=pgvector
PGVECTOR_CONNECTION_STRING=postgresql+asyncpg://user:pass@host/db

# Qdrant (high-performance)
VECTOR_STORE_TYPE=qdrant
QDRANT_URL=http://localhost:6333

# Pinecone (managed cloud)
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=your-index
```

Install optional dependencies:

```bash
pip install -e ".[pgvector]"   # PGVector
pip install -e ".[qdrant]"     # Qdrant
pip install -e ".[pinecone]"   # Pinecone
pip install -e ".[all]"        # Everything
```

---

## Cloud Fallback

When `LLM_FALLBACK_MODEL` is set, AdaptiveAgent uses **LiteLLM Router** for automatic provider switching:

```bash
# Enable cloud fallback
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
LLM_FALLBACK_MODEL=gpt-4o-mini
LLM_FALLBACK_API_KEY=sk-...
```

**What triggers fallback:**
- Ollama connection refused (server not running)
- Timeout (slow inference, VRAM thrashing)
- HTTP 503 (overloaded), 5xx errors
- Rate limiting

**Features:**
- Per-deployment retry before fallback
- 60-second cooldown on degraded backends
- Transparent to all graph nodes — `get_llm()` API unchanged
- Supports OpenAI, Anthropic, Google, Groq as fallback providers

---

## Evaluation Framework

AdaptiveAgent includes two evaluation layers:

### 1. In-Pipeline Evaluation (eval_node)

Runs automatically after every response generation:

- **Heuristic scoring** — response length, evidence grounding, query relevance (zero cost)
- **Ragas-style faithfulness** — LLM extracts claims, verifies each against context via NLI
- **Answer relevancy** — LLM scores whether the response addresses the query
- **Combined score** — weighted blend; if below `eval_threshold`, triggers refine loop

### 2. Standalone Ragas API (`POST /evaluate`)

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "question": "What is RAG?",
    "answer": "RAG combines retrieval with generation...",
    "contexts": ["Retrieval Augmented Generation (RAG) is a technique..."]
  }'
```

**Response:**
```json
{
  "faithfulness": 0.92,
  "answer_relevancy": 0.88,
  "context_precision": 0.0,
  "context_recall": 0.0,
  "ragas_score": 0.90,
  "judge_model": "qwen2.5:7b"
}
```

Add `ground_truth` to enable context_precision and context_recall metrics.

---

## Development Workflow

```bash
# Lint
cd backend && ruff check app/ tests/ --no-fix

# Format
cd backend && ruff format app/ tests/

# Tests (94 tests)
cd backend && python -m pytest tests/ -v

# Frontend typecheck
cd frontend && npx tsc --noEmit

# Frontend lint
cd frontend && npx next lint
```

---

## Testing

The backend test suite (**94 tests**) covers:

| Category | Coverage |
|----------|----------|
| **Routing matrix** | All conditional edges (validation, planner, retrieval, evidence, confidence, risk, approval, tools, eval) |
| **Tool routing** | Error handling, circuit breaker, refine on failure, success paths |
| **Approval matrix** | Risk levels, tool counts, plan sizes vs auto-approve/pending |
| **Confidence scoring** | 3-factor model (term coverage, doc count, credibility) |
| **Risk assessment** | 10-factor model with configurable thresholds |
| **Evidence verification** | Coverage, contradictions, credibility, missing terms |
| **Retrieval** | BM25, embedding cache, reranker parsing |
| **Nodes** | Refine (LLM + deterministic fallback), reasoning fallback, eval node |
| **Judge service** | Heuristic fallback, eval disabled, Ragas faithfulness |
| **Integration** | Full graph execution, chat helpers, thread management |

```bash
cd backend && python -m pytest tests/ -v
```

---

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/chat` | POST | API Key | Send message, get SSE stream or complete response |
| `/chat/approve` | POST | API Key | Approve or reject tool execution |
| `/chat/pending` | GET | API Key | List pending approval requests |
| `/upload` | POST | API Key | Upload document (txt, md, pdf, docx) |
| `/evaluate` | POST | API Key | Evaluate RAG response with Ragas metrics |
| `/audit` | GET | API Key | Query audit logs |
| `/health` | GET | — | System health check (Ollama, ChromaDB, PostgreSQL) |
| `/docs` | GET | — | OpenAPI documentation |

---

## Security

| Layer | Mechanism |
|-------|-----------|
| **Input validation** | Query length limits, empty query detection |
| **Prompt injection** | Sunglasses engine + structural SQL injection patterns |
| **PII detection** | SSN, credit card, email pattern matching |
| **Output safety** | Blocked phrase detection on generated responses |
| **Auth** | `X-API-Key` header with `hmac.compare_digest` (timing-attack safe) |
| **Risk gating** | 10-factor risk model triggers human-in-the-loop approval |
| **Circuit breaker** | `max_steps` prevents infinite retry loops |
| **File upload** | 50MB size limit, extension whitelist (.txt, .md, .pdf, .docx) |
| **Tool sandboxing** | `read_file` restricted to allowed directories, 1MB read cap |
| **Thread isolation** | Each conversation uses a unique `thread_id` |

**Production checklist:**

- [ ] Set `API_KEY` for authentication
- [ ] Change `AUTH_JWT_SECRET` from default
- [ ] Configure `LLM_PROVIDER` and API keys
- [ ] Enable HTTPS (reverse proxy with nginx/caddy)
- [ ] Set `CORS_ORIGINS` to your frontend domain
- [ ] Review `MAX_STEPS` and risk thresholds
- [ ] Configure `EVAL_JUDGE_MODEL` for evaluation
- [ ] Set up vector store backend for production (PGVector/Qdrant/Pinecone)

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Support

If you run into issues or want to discuss improvements, open an issue or start a discussion on GitHub.
