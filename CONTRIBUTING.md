# Contributing to AdaptiveAgent

Thank you for helping improve AdaptiveAgent.

## Development workflow

1. Fork the repository and create a feature branch.
2. Install backend and frontend dependencies.
3. Make focused changes with clear commit messages.
4. Run available tests and linters before opening a pull request.
5. Submit a pull request with a concise summary and testing notes.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests -v
```

## Frontend

```bash
cd frontend
npm install
npm run lint
npm run typecheck
```

## Code style

- Use clear, descriptive names.
- Keep changes focused and easy to review.
- Prefer small, well-tested commits.
