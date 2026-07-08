# Contributing to AdaptiveAgent

Thank you for helping improve AdaptiveAgent.

## Development workflow

1. Fork the repository and create a feature branch from main.
2. Install backend and frontend dependencies.
3. Make focused changes with clear commit messages.
4. Run available tests and linters before opening a pull request.
5. Submit a pull request with a concise summary and testing notes.

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests -v
```

## Frontend setup

```bash
cd frontend
npm install
npm run lint
npm run typecheck
```

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
