# AdaptiveAgent

![CI](https://github.com/YogendraChukka01/AdaptiveAgent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)

AdaptiveAgent is a secure, explainable, and trustworthy agentic RAG platform for building context-aware assistants on top of private knowledge bases.

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

## Overview

AdaptiveAgent combines retrieval, reasoning, confidence scoring, risk checks, and approval flows in a single platform. It is designed for teams building internal copilots, knowledge assistants, and policy-aware AI experiences on private document collections.

## Features

- Document ingestion and retrieval pipelines
- Hybrid search with vector and keyword strategies
- Evidence-grounded reasoning and response generation
- Confidence and risk evaluation for safer agent behavior
- Approval and tool execution stages for controlled workflows
- FastAPI backend and Next.js frontend with Docker-based local deployment

## Architecture

- Backend: FastAPI + LangGraph + Ollama + ChromaDB
- Frontend: Next.js + TypeScript + Tailwind CSS
- Infrastructure: Docker Compose for local development and orchestration

## Project structure

```text
backend/        Python API, graph orchestration, and services
frontend/       Next.js UI and client-side integration
infra/          Docker Compose and deployment helpers
docs/           Project documentation and design notes
.github/        CI workflows, issue templates, and PR templates
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

## Configuration

Copy the example environment file before running the backend:

```bash
cp .env.example .env
```

Key variables include:

- OLLAMA_MODEL
- OLLAMA_BASE_URL
- CHROMA_PERSIST_DIRECTORY
- POSTGRES_URL
- REDIS_URL
- AUTH_JWT_SECRET

## Development workflow

```bash
# Backend tests
cd backend && python -m pytest tests -v

# Frontend linting
cd frontend && npm run lint

# Frontend type checking
cd frontend && npm run typecheck
```

## Testing

The project includes backend tests under the backend test suite. Add or extend tests for:

- retrieval and ranking behavior
- graph node transitions
- risk and confidence scoring decisions
- chat API streaming responses

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

If you run into issues or want to discuss improvements, open an issue or start a discussion on GitHub.
