# AdaptiveAgent

AdaptiveAgent is a secure, explainable, and trustworthy agentic RAG platform for building context-aware assistants on top of private knowledge bases.

## Why this project matters

- Provides a production-minded architecture for retrieval-augmented generation workflows.
- Combines retrieval, reasoning, confidence scoring, risk checks, and approval flows in one platform.
- Designed to be extensible for enterprise copilots, internal knowledge assistants, and regulated environments.

## Key capabilities

- Document ingestion and retrieval pipelines
- Hybrid search with vector and keyword strategies
- Evidence-grounded reasoning and response generation
- Confidence and risk evaluation for safer agent behavior
- Approval and tool execution stages for controlled workflows
- FastAPI backend and Next.js frontend with Docker-based local deployment

## Architecture at a glance

- Backend: FastAPI + LangGraph + Ollama + ChromaDB
- Frontend: Next.js + TypeScript + Tailwind CSS
- Infrastructure: Docker Compose for local development and orchestration

## Project structure

```text
backend/       Python API and graph orchestration
frontend/      Next.js user interface
infra/         Docker and deployment configuration
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- Git

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

### 4. Run locally

```bash
cd ../infra
docker compose up -d
```

You can then access the application through the configured frontend and API endpoints.

## Development commands

```bash
# Backend tests
cd backend && python -m pytest tests -v

# Frontend linting
cd frontend && npm run lint

# Full stack with Docker
cd infra && docker compose up -d --build
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
