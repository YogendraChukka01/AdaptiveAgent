# ── Builder stage ─────────────────────────────────────────────────────────────
# Fix I-06: pin to minor version (no digest here for readability,
# but in production add @sha256:<digest>)
FROM python:3.12-slim AS builder

# Install OS build deps (including libpq-dev for psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
# Install runtime deps into a prefix we can copy to the final stage
RUN pip install --no-cache-dir --prefix=/install "."

COPY . .

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Non-root user
RUN groupadd --gid 1001 safeagent \
    && useradd --uid 1001 --gid safeagent --no-create-home safeagent \
    && chown -R safeagent:safeagent /app

USER safeagent

EXPOSE 8000

# Healthcheck directly in image
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--timeout-keep-alive", "65", \
     "--workers", "1"]
