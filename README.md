# AdaptiveAgent

![CI](https://github.com/YogendraChukka01/AdaptiveAgent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)

**AdaptiveAgent** is a secure, explainable, and trustworthy **Agentic RAG** platform for building context-aware assistants on top of private knowledge bases. It pairs a LangGraph-orchestrated reasoning pipeline with a Next.js frontend and a Docker-based local stack.

The codebase is verified locally with the backend test suite and a production frontend build.

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
- **Self-correcting retrieval.** When evidence or confidence is weak, the agent *refines* the query and widens retrieval rather than repeating the same failed search (Corrective RAG / Self-RAG "repair" step).

---

## Features

- Document ingestion and hybrid retrieval (dense vector + BM25 keyword + reranking)
- Evidence-grounded reasoning with explicit reasoning traces
- Confidence and risk evaluation for safer agent behavior
- Approval gating and tool execution for controlled workflows
- A self-correcting retry loop that rewrites/broadens queries on weak results
- FastAPI backend with streaming (SSE) and a Next.js + TypeScript frontend
- Docker Compose stack for local development and orchestration

---

## Architecture

**Backend** — FastAPI + LangGraph + Ollama + ChromaDB (BGE-M3 embeddings, BM25, BGE reranker).

The agent is modelled as a stateful, cyclic LangGraph. The happy path is:

```
validator → planner → tool_planner → retrieval → evidence →
reasoning → confidence → risk → approval → tools → response
```

**Self-correction.** If `evidence_coverage` or `confidence_score` is below its threshold (or a tool fails) and the `step_count` circuit breaker has not been reached, the graph routes to the `refine` node instead of re-running validation/planning/approval with the identical query. `refine` rewrites/broadens the query (LLM with a deterministic fallback) and `retrieval` widens its candidate `k` on later attempts, so retries are productive and bounded by `max_steps`.

**Thread isolation.** Every request uses a unique `thread_id` with a PostgresSaver checkpointer, so conversations and approval pauses are isolated and resumable.

**Frontend** — Next.js 15 + TypeScript + Tailwind CSS.

**Infrastructure** — Docker Compose for Postgres, Redis, Ollama, the backend, and the frontend.

---

## Project structure

```text
backend/        Python API, LangGraph orchestration, and services
frontend/       Next.js UI and client-side integration
infra/          Docker Compose and deployment helpers
docs/           Project documentation and design notes
.github/        CI workflows, issue templates, and PR templates
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

### Example API call

```bash
curl http://localhost:8000/health
```

---

## Configuration

Copy the example environment file before running the backend:

```bash
cp .env.example .env
```

Key variables include:

- `OLLAMA_MODEL` — chat/tool-calling model (e.g. `qwen2.5:7b`)
- `OLLAMA_BASE_URL` — Ollama endpoint
- `CHROMA_PERSIST_DIRECTORY` — vector store path
- `POSTGRES_URL` — checkpointer database
- `REDIS_URL` — approval/tracking cache
- `AUTH_JWT_SECRET` — API auth secret (change before production)
- `MAX_STEPS` — retry circuit-breaker bound
- `EVIDENCE_THRESHOLD` / `CONFIDENCE_RETRY_THRESHOLD` — self-correction gates

See `.env.example` for the full list.

---

## Development workflow

```bash
# Backend tests
cd backend && python -m pytest -q

# Frontend build
cd frontend && npm run build

# Frontend linting
cd frontend && npm run lint

# Frontend type checking
cd frontend && npm run typecheck
```

Code quality for the backend is enforced with `ruff` (lint + format). Run `ruff check app tests` and `ruff format app tests` before committing.

---

## Testing

The backend test suite covers:

- Planner and reasoning fallback behavior (LLM-unavailable paths)
- Retrieval, ranking, and embedding cache behavior
- Graph node transitions and the routing/retry matrix
- Risk and confidence scoring decisions
- The `refine` self-correction node (LLM rewrite + deterministic fallback)
- Chat API payload helpers and approval interrupt/resume

Run the suite with:

```bash
cd backend && python -m pytest -q
```

Embedding/reranker providers that require an external API are skipped automatically when the network is unavailable.

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Support

If you run into issues or want to discuss improvements, open an issue or start a discussion on GitHub.
