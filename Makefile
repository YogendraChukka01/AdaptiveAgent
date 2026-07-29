# ============================================================
# AdaptiveAgent — Makefile
# ============================================================
# Cross-platform commands for development, testing, and deployment.
# Usage: make <target>
# ============================================================

.PHONY: help setup dev test lint format clean docker-up docker-down docker-build

SHELL := /bin/bash

# ── Help ─────────────────────────────────────────────────────
help: ## Show this help message
	@echo ""
	@echo "  AdaptiveAgent — Available Commands"
	@echo "  ==================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Setup ────────────────────────────────────────────────────
setup: ## Full project setup (backend + frontend)
	@bash scripts/setup.sh

setup-backend: ## Setup backend only
	cd backend && python3 -m venv .venv && \
		source .venv/bin/activate && \
		pip install --upgrade pip && \
		pip install -e ".[dev]" && \
		cp -n .env.example .env 2>/dev/null || true

setup-frontend: ## Setup frontend only
	cd frontend && npm ci

# ── Development ──────────────────────────────────────────────
dev-backend: ## Start backend dev server (with auto-reload)
	cd backend && source .venv/bin/activate && \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev

dev-services: ## Start infrastructure services only (Postgres, Redis, Ollama)
	docker compose -f infra/docker-compose.yml up postgres redis ollama

# ── Testing ──────────────────────────────────────────────────
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v

test-backend-cov: ## Run backend tests with coverage
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend: ## Run frontend typecheck + lint
	cd frontend && npx tsc --noEmit && npx next lint

# ── Linting & Formatting ────────────────────────────────────
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend with ruff
	cd backend && ruff check app/ tests/ --no-fix

lint-frontend: ## Lint frontend with eslint
	cd frontend && npx next lint

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend with ruff
	cd backend && ruff format app/ tests/

format-frontend: ## Format frontend with prettier (if installed)
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

typecheck: ## Run type checks
	cd backend && mypy app/ --ignore-missing-imports
	cd frontend && npx tsc --noEmit

# ── Docker ───────────────────────────────────────────────────
docker-up: ## Start full Docker stack
	docker compose -f infra/docker-compose.yml up -d --build

docker-down: ## Stop Docker stack
	docker compose -f infra/docker-compose.yml down

docker-build: ## Build Docker images
	docker compose -f infra/docker-compose.yml build

docker-logs: ## View Docker logs
	docker compose -f infra/docker-compose.yml logs -f

docker-reset: ## Stop and remove all data (volumes)
	docker compose -f infra/docker-compose.yml down -v

# ── Database ─────────────────────────────────────────────────
db-shell: ## Connect to PostgreSQL shell
	docker compose -f infra/docker-compose.yml exec postgres psql -U safeagent -d safeagent

# ── Verification ─────────────────────────────────────────────
verify: ## Verify all prerequisites and setup
	@bash scripts/verify.sh

# ── Clean ────────────────────────────────────────────────────
clean: ## Remove build artifacts and caches
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find backend -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find frontend -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	echo "Cleaned!"

clean-all: clean ## Remove everything including venvs and node_modules
	rm -rf backend/.venv frontend/node_modules
	echo "Full clean done!"
