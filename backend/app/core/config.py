from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "SafeAgent"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://safeagent:safeagent@localhost:5432/safeagent"
    database_url_sync: str = "postgresql://safeagent:safeagent@localhost:5432/safeagent"
    redis_url: str = "redis://localhost:6379/0"

    # ── Primary LLM provider ──────────────────────────────────────────
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str | None = None
    llm_api_key: str | None = None

    # ── Cloud fallback (tried if primary fails) ───────────────────────
    llm_fallback_model: str | None = None
    llm_fallback_api_key: str | None = None
    llm_fallback_base_url: str | None = None
    llm_fallback_provider: str | None = None

    # ── LiteLLM behaviour knobs ───────────────────────────────────────
    llm_request_timeout: int = 60
    llm_num_retries: int = 2
    llm_fallback_num_retries: int = 1

    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "BAAI/bge-m3"
    ollama_reranker_model: str = "BAAI/bge-reranker-v2-m3"

    embedding_provider: str = "bge"
    embedding_model: str = "BAAI/bge-m3"
    embedding_api_base: str | None = None
    embedding_api_key: str | None = None

    reranker_provider: str = "bge"
    reranker_api_base: str | None = None
    reranker_api_key: str | None = None

    chroma_persist_directory: str = "./chroma_data"

    # ── Vector store backend ─────────────────────────────────────────
    vector_store_type: str = "chroma"
    vector_store_collection: str = "safeagent_docs"
    pgvector_connection_string: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_grpc: bool = False
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""

    auth_jwt_secret: str = ""
    auth_jwt_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 60

    # API key for authenticating API clients (X-API-Key header).
    # Leave empty to disable auth (dev mode).
    api_key: str = ""

    max_steps: int = 10
    max_tokens_per_response: int = 4096
    llm_cache_enabled: bool = True
    # Retry threshold on the 0-100 confidence scale returned by calculate_confidence.
    confidence_retry_threshold: float = 30.0
    high_risk_threshold: float = 70.0

    evidence_threshold: float = 0.3
    evidence_min_coverage: float = 0.5
    evidence_min_docs: int = 3
    evidence_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "term_coverage": 0.40,
            "doc_count": 0.25,
            "credibility": 0.35,
        }
    )

    max_query_length: int = 10000

    # ── Evaluation node ───────────────────────────────────────────────
    eval_enabled: bool = True
    eval_threshold: float = 0.85
    eval_judge_model: str | None = None
    eval_judge_api_key: str | None = None
    eval_judge_base_url: str | None = None
    eval_judge_max_chars: int = 1500
    eval_ragas_enabled: bool = True
    eval_relevancy_enabled: bool = True

    # ── Memory distillation ───────────────────────────────────────────
    memory_distill_enabled: bool = True
    memory_distill_interval_minutes: int = 30
    memory_distill_max_messages: int = 200

    langsmith_api_key: str | None = None
    langsmith_project: str = "safeagent"

    approval_ttl_seconds: int = 86400

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )


settings = Settings()
