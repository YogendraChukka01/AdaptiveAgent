from __future__ import annotations

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

    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str | None = None
    llm_api_key: str | None = None

    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "BAAI/bge-m3"
    ollama_reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Embedding backend. "bge" (FlagEmbedding, default) or "openai"
    # (any OpenAI-compatible embeddings API: Ollama /v1/embeddings, vLLM,
    # Together, OpenAI, ...). For "openai", set embedding_api_base /
    # embedding_api_key if not using api.openai.com.
    embedding_provider: str = "bge"
    embedding_model: str = "BAAI/bge-m3"
    embedding_api_base: str | None = None
    embedding_api_key: str | None = None

    # Reranker backend. "bge" (FlagEmbedding, default) or "rest"
    # (any Jina/Cohere/Voyage-shaped rerank API; set reranker_api_base).
    reranker_provider: str = "bge"
    reranker_api_base: str | None = None
    reranker_api_key: str | None = None

    chroma_persist_directory: str = "./chroma_data"

    auth_jwt_secret: str = "change-me-in-production"
    auth_jwt_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 60

    max_steps: int = 10
    max_tokens_per_response: int = 4096
    llm_cache_enabled: bool = True
    confidence_threshold: float = 0.7
    # Retry threshold on the 0-100 confidence scale returned by calculate_confidence.
    confidence_retry_threshold: float = 30.0
    high_risk_threshold: float = 70.0

    evidence_threshold: float = 0.3
    evidence_min_coverage: float = 0.5
    evidence_min_docs: int = 3
    evidence_weights: dict[str, float] = {
        "term_coverage": 0.40,
        "doc_count": 0.25,
        "credibility": 0.35,
    }

    max_query_length: int = 10000

    langsmith_api_key: str | None = None
    langsmith_project: str = "safeagent"

    # Seconds an approval request is considered live before it is treated as
    # expired (see app.core.threads). 0 disables expiry tracking.
    approval_ttl_seconds: int = 86400

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
