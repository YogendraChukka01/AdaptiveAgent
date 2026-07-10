from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_llm_cache: object | None = None


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


def get_llm(
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> object:
    """Return a LangChain chat model with automatic cloud fallback.

    If ``llm_fallback_model`` is configured and the primary model is
    ``ollama``, a ``ChatLiteLLM`` wrapper is used.  LiteLLM handles the
    fallback chain natively: primary → fallback on failure.
    """
    provider = settings.llm_provider.lower()
    model = settings.llm_model
    api_key = settings.llm_api_key
    base_url = settings.llm_base_url

    has_fallback = bool(settings.llm_fallback_model)

    if has_fallback:
        try:
            from langchain_litellm import ChatLiteLLM

            primary_model = _litellm_model_id(provider, model, base_url)
            fallback_model = _litellm_model_id(
                settings.llm_fallback_provider or "openai",
                settings.llm_fallback_model,
                settings.llm_fallback_base_url,
            )

            fallbacks = [fallback_model]
            logger.info("Using LiteLLM with fallback: %s -> %s", primary_model, fallback_model)

            kwargs: dict = {
                "model": primary_model,
                "temperature": temperature,
                "num_retries": settings.llm_num_retries,
                "fallbacks": fallbacks,
                "request_timeout": settings.llm_request_timeout,
                "drop_params": True,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            if api_key:
                kwargs["api_key"] = api_key
            if base_url:
                kwargs["api_base"] = base_url

            return ChatLiteLLM(**kwargs)
        except ImportError:
            logger.warning(
                "langchain_litellm not installed; falling back to direct provider. "
                "Install with: pip install langchain-litellm"
            )

    return _build_langchain_llm(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


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
