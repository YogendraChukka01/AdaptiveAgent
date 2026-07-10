FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install backend Python dependencies
COPY backend/pyproject.toml /tmp/backend/pyproject.toml
RUN pip install --no-cache-dir -e /tmp/backend/ 2>/dev/null || pip install --no-cache-dir fastapi uvicorn[standard] langgraph langchain-core pydantic pydantic-settings redis chromadb httpx psycopg psycopg-pool asyncpg 2>/dev/null || true

# Pre-install frontend node_modules
COPY frontend/package.json frontend/package-lock.json* /tmp/frontend/
WORKDIR /tmp/frontend && npm install 2>/dev/null || true

EXPOSE 3000 8000 11434 5432
