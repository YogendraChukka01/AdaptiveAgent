from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _install_cache() -> None:
    """Enable LangChain's in-memory LLM cache when configured."""
    if not settings.llm_cache_enabled:
        return
    try:
        from langchain_core.caches import InMemoryCache
        from langchain_core.globals import set_llm_cache

        set_llm_cache(InMemoryCache())
    except Exception:
        logger.debug("LLM cache setup failed; caching disabled")


_install_cache()


def _build_langchain_llm(
    provider: str,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> object:
    """Build a LangChain chat model for a given provider."""
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            base_url=base_url or settings.ollama_base_url,
            temperature=temperature,
            num_predict=max_tokens,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    msg = f"Unknown llm_provider '{provider}'. Supported: ollama, openai, anthropic, google, groq"
    raise ValueError(msg)


def _litellm_model_id(provider: str, model: str, base_url: str | None = None) -> str:
    """Build a LiteLLM model identifier from provider + model name."""
    if provider == "ollama":
        prefix = "ollama_chat/" if "/" not in model else ""
        return f"{prefix}{model}"
    if provider in ("openai", "anthropic", "google", "groq"):
        prefix = f"{provider}/" if "/" not in model else ""
        return f"{prefix}{model}"
    if base_url:
        return f"openai/{model}"
    return model


def _build_router_llm(
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> object:
    """Build a ChatLiteLLMRouter with automatic cloud fallback.

    Uses litellm.Router for production-grade fallback handling:
    - Automatic retry on timeout, 5xx, rate-limit errors
    - Cooldown on degraded deployments
    - Transparent fallback: ollama → cloud model
    """
    from langchain_litellm import ChatLiteLLMRouter
    from litellm import Router

    provider = settings.llm_provider.lower()
    model = settings.llm_model
    api_key = settings.llm_api_key
    base_url = settings.llm_base_url

    primary_model = _litellm_model_id(provider, model, base_url)
    fallback_model = _litellm_model_id(
        settings.llm_fallback_provider or "openai",
        settings.llm_fallback_model or "gpt-4o-mini",
        settings.llm_fallback_base_url,
    )

    model_list = [
        {
            "model_name": "chat",
            "litellm_params": {
                "model": primary_model,
                "temperature": temperature,
                "request_timeout": settings.llm_request_timeout,
                "num_retries": settings.llm_num_retries,
                "drop_params": True,
                **({"api_key": api_key} if api_key else {}),
                **({"api_base": base_url} if base_url else {}),
            },
        },
        {
            "model_name": "chat",
            "litellm_params": {
                "model": fallback_model,
                "temperature": temperature,
                "request_timeout": 30,
                "num_retries": settings.llm_fallback_num_retries,
                "drop_params": True,
                **(
                    {"api_key": settings.llm_fallback_api_key}
                    if settings.llm_fallback_api_key
                    else {}
                ),
                **(
                    {"api_base": settings.llm_fallback_base_url}
                    if settings.llm_fallback_base_url
                    else {}
                ),
            },
        },
    ]

    router = Router(
        model_list=model_list,
        fallbacks=[{"chat": ["chat"]}],
        num_retries=1,
        retry_after=2,
        timeout=settings.llm_request_timeout + 15,
        routing_strategy="simple-shuffle",
        allowed_fails=3,
        cooldown_time=60,
    )

    kwargs: dict = {
        "router": router,
        "model": "chat",
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    logger.info(
        "Using litellm.Router fallback: %s -> %s",
        primary_model,
        fallback_model,
    )

    return ChatLiteLLMRouter(**kwargs)


def get_llm(
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> object:
    """Return a LangChain chat model with automatic cloud fallback.

    When ``llm_fallback_model`` is configured, uses litellm.Router for
    production-grade fallback handling (retry, cooldown, transparent
    provider switching).  Ollama timeouts, connection errors, and VRAM
    exhaustion automatically trigger fallback to the cloud model.
    """
    has_fallback = bool(settings.llm_fallback_model)

    if has_fallback:
        try:
            return _build_router_llm(temperature=temperature, max_tokens=max_tokens)
        except ImportError:
            logger.warning(
                "langchain_litellm not installed; falling back to direct provider. "
                "Install with: pip install langchain-litellm"
            )

    provider = settings.llm_provider.lower()
    return _build_langchain_llm(
        provider=provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
