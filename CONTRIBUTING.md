# Contributing to AdaptiveAgent

Thank you for helping improve AdaptiveAgent.

Please review our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Development workflow

1. Fork the repository and create a feature branch from main.
2. Install backend and frontend dependencies.
3. Set up your environment.
4. Make focused changes with clear commit messages.
5. Run available tests and linters before opening a pull request.
6. Submit a pull request with a concise summary and testing notes.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose (optional, for full stack)

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # edit with your settings
python -m pytest tests -v
```

## Frontend setup

```bash
cd frontend
npm install
npm run lint
npm run typecheck
```

## Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

## Docker setup (optional)

```bash
docker compose -f infra/docker-compose.yml up -d
```

This starts PostgreSQL, Redis, Ollama, backend, and frontend.

## Coding standards

- Use clear, descriptive names.
- Keep changes focused and easy to review.
- Prefer small, well-tested commits.
- Avoid committing secrets, credentials, or local environment files.
- Follow the existing project conventions for Python and TypeScript.

## Commit message conventions

Use concise, descriptive commit messages such as:

- feat: add new retrieval strategy
- fix: correct chat streaming error handling
- docs: improve contributor guidance
- chore: update CI and tooling

## Pull request expectations

- Include a summary of the change and why it matters.
- Reference related issues when applicable.
- Include relevant testing details.
- Keep PRs scoped to a single concern where possible.
