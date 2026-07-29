# AdaptiveAgent

![CI](https://github.com/YogendraChukka01/AdaptiveAgent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Tests](https://img.shields.io/badge/tests-94%20passed-brightgreen)

**AdaptiveAgent** is a production-grade, secure, and explainable **Agentic RAG** platform for building context-aware assistants on private knowledge bases. It combines a LangGraph-orchestrated reasoning pipeline with a Next.js frontend, multi-vector store support, LLM-as-judge evaluation, and automatic cloud fallback — all in a Docker-based local stack.

---

## Table of Contents

- [Quick Start](#quick-start)
  - [Docker Setup (Recommended)](#docker-setup-recommended)
  - [Local Development Setup](#local-development-setup)
- [Prerequisites](#prerequisites)
- [Platform-Specific Setup](#platform-specific-setup)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
- [Verify Installation](#verify-installation)
- [Development](#development)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

### Docker Setup (Recommended)

Get the entire stack running in one command:

```bash
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent
cp backend/.env.example backend/.env
cd infra && docker compose up -d --build
```

Wait ~2 minutes for models to download, then open:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

### Local Development Setup

For faster iteration with hot-reload:

```bash
# 1. Clone
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent

# 2. One-command setup (installs everything)
bash scripts/setup.sh        # macOS / Linux
.\scripts\setup.ps1          # Windows (PowerShell)

# 3. Start services (Postgres, Redis, Ollama)
docker compose -f infra/docker-compose.yml up postgres redis ollama -d

# 4. Start backend (Terminal 1)
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload

# 5. Start frontend (Terminal 2)
cd frontend && npm run dev
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 20+ | Frontend build |
| **Docker** | 24+ | Services (Postgres, Redis, Ollama) |
| **Docker Compose** | v2+ | Container orchestration |
| **Git** | 2.30+ | Version control |

---

## Platform-Specific Setup

### Windows

**Option A — Automated (Recommended)**

```powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent
.\scripts\setup.ps1
```

**Option B — Manual**

```powershell
# 1. Install prerequisites (if not already installed)
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
winget install Docker.DockerDesktop

# 2. Clone and setup
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent

# 3. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
cd ..

# 4. Frontend
cd frontend
npm ci
cd ..

# 5. Start services
docker compose -f infra/docker-compose.yml up postgres redis ollama -d
```

**Windows-Specific Notes:**
- Use PowerShell 7+ (`pwsh`) for best cross-platform compatibility
- If using WSL2, you can follow the Linux instructions instead
- Docker Desktop must be running before starting services
- Use `.\venv\Scripts\activate` instead of `source .venv/bin/activate`

### macOS

**Option A — Automated (Recommended)**

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Clone and setup
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent
bash scripts/setup.sh
```

**Option B — Manual**

```bash
# 1. Install prerequisites
brew install python@3.12 node@22 git

# 2. Install Docker Desktop
brew install --cask docker

# 3. Clone and setup
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent

# 4. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
cd ..

# 5. Frontend
cd frontend
npm ci
cd ..

# 6. Start services
docker compose -f infra/docker-compose.yml up postgres redis ollama -d
```

**macOS-Specific Notes:**
- Apple Silicon (M1/M2/M3) is fully supported
- Ollama runs natively on macOS — no Docker needed for inference
- Use `brew install ollama` for local Ollama instead of Docker

### Linux (Ubuntu/Debian)

**Option A — Automated (Recommended)**

```bash
# Clone and setup
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent
bash scripts/setup.sh
```

**Option B — Manual**

```bash
# 1. Install prerequisites
sudo apt update && sudo apt install -y \
    python3.12 python3.12-venv python3-pip \
    nodejs npm \
    git curl

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect

# 2. Clone and setup
git clone https://github.com/YogendraChukka01/AdaptiveAgent.git
cd AdaptiveAgent

# 3. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
cd ..

# 4. Frontend
cd frontend
npm ci
cd ..

# 5. Start services
docker compose -f infra/docker-compose.yml up postgres redis ollama -d
```

**Linux-Specific Notes:**
- Add your user to the `docker` group to run Docker without `sudo`
- For GPU-accelerated Ollama, install NVIDIA Container Toolkit
- On headless servers, use `npm ci` without a browser

---

## Verify Installation

Run the verification script to ensure everything is set up correctly:

```bash
bash scripts/verify.sh
# or
make verify
```

This checks:
- System tools (Git, Python, Node.js, Docker)
- Backend dependencies and virtual environment
- Frontend dependencies and TypeScript compilation
- Configuration files

---

## Development

### Using Make (Recommended)

```bash
make help              # Show all available commands
make setup             # Full project setup
make dev-backend       # Start backend with auto-reload
make dev-frontend      # Start frontend dev server
make dev-services      # Start Postgres, Redis, Ollama
make test              # Run all tests
make lint              # Run linters
make format            # Format all code
make docker-up         # Start full Docker stack
make docker-down       # Stop Docker stack
make clean             # Remove build artifacts
```

### Manual Commands

```bash
# Backend
cd backend && source .venv/bin/activate
ruff check app/ tests/ --no-fix    # Lint
ruff format app/ tests/            # Format
python -m pytest tests/ -v         # Test
mypy app/ --ignore-missing-imports # Type check

# Frontend
cd frontend
npx tsc --noEmit                   # Type check
npx next lint                      # Lint
npm run dev                        # Dev server
npm run build                      # Production build
```

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
                 │  step_counter → validator → planner →         │
                 │  tool_planner → retrieval → evidence →        │
                 │  reasoning → confidence → risk → approval →   │
                 │  tools → response → eval → [refine | END]    │
                 └──┬──────────┬──────────┬──────────┬──────────┘
                    │          │          │          │
            ┌───────▼──┐ ┌────▼────┐ ┌───▼───┐ ┌───▼────────┐
            │ Ollama /  │ │ Vector  │ │ Redis │ │ PostgreSQL │
            │ LiteLLM   │ │ Store   │ │       │ │            │
            │ Router    │ │ (multi) │ │       │ │            │
            └───────────┘ └─────────┘ └───────┘ └────────────┘
```

---

## Configuration

All settings are configured via environment variables or `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama`, `openai`, `anthropic`, `google`, `groq` |
| `LLM_MODEL` | `qwen2.5:7b` | Chat model name |
| `VECTOR_STORE_TYPE` | `chroma` | Backend: `chroma`, `pgvector`, `qdrant`, `pinecone` |
| `EVAL_ENABLED` | `true` | Enable post-generation evaluation |
| `API_KEY` | `""` | API key for auth (empty = dev mode) |
| `MAX_STEPS` | `10` | Retry circuit-breaker bound |

See `backend/.env.example` for the full list.

---

## Testing

```bash
# Run all tests (94 tests)
make test

# Backend tests only
make test-backend

# With coverage
make test-backend-cov

# Frontend checks only
make test-frontend
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `docker: command not found` | Install Docker Desktop or Docker Engine |
| `python: command not found` | Install Python 3.12+ and add to PATH |
| `node: command not found` | Install Node.js 22+ from nodejs.org |
| Port 8000 already in use | `lsof -ti:8000 \| xargs kill -9` (macOS/Linux) |
| Ollama not responding | `docker compose -f infra/docker-compose.yml logs ollama` |
| Permission denied (Linux) | Add user to docker group: `sudo usermod -aG docker $USER` |
| Frontend can't reach backend | Ensure backend is running on port 8000 |

### Getting Help

```bash
make verify          # Check your setup
make docker-logs     # View service logs
docker compose -f infra/docker-compose.yml ps  # Check service status
```

If issues persist, open an issue at https://github.com/YogendraChukka01/AdaptiveAgent/issues

---

## Project Structure

```text
backend/
  app/
    api/                  FastAPI routes (chat, upload, health, audit, evaluate)
    core/                 Config, auth, database, dependencies
    graph/
      builder.py          LangGraph StateGraph compilation (14 nodes)
      edges/              Conditional routing functions
      nodes/              One file per graph node
    models/               Pydantic state/request/response schemas
    services/             LLM, retrieval, confidence, risk, audit
  tests/                  94 tests

frontend/
  src/
    app/                  Next.js pages
    components/           Chat UI components
    lib/                  API client (SSE streaming)

infra/                    Docker Compose, monitoring
scripts/                  Setup and verification scripts
.github/                  CI workflows
```

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
