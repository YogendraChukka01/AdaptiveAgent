from __future__ import annotations

from app.core.config import settings


def _install_cache() -> None:
    """Enable LangChain's in-memory LLM cache when configured.

    Caching identical prompts (planner/tool-planner/reasoning calls) avoids
    redundant model round-trips and cost. Disabled by default-safe flag.
    """
    if not settings.llm_cache_enabled:
        return
    try:
        from langchain_core.caches import InMemoryCache
        from langchain_core.globals import set_llm_cache

        set_llm_cache(InMemoryCache())
    except Exception:
        # Caching is a best-effort optimisation; never fail startup over it.
        pass


_install_cache()


def get_llm(
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> object:
    provider = settings.llm_provider.lower()
    model = settings.llm_model
    api_key = settings.llm_api_key
    base_url = settings.llm_base_url

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
