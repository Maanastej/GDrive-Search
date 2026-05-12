"""
LLM Service — factory for chat model instances.

Abstracts away the choice between OpenAI and Anthropic so that
the rest of the codebase can remain provider-agnostic.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_chat_model() -> BaseChatModel:
    """
    Return a configured LangChain chat model based on application settings.

    Supports:
        - ``openai``   → ChatOpenAI  (GPT-4o, GPT-4-turbo, etc.)
        - ``anthropic`` → ChatAnthropic (Claude 3.5 Sonnet, Opus, etc.)
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        model = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
        )
        logger.info("LLM: OpenAI %s", settings.LLM_MODEL)

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )

        model = ChatAnthropic(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.ANTHROPIC_API_KEY,
        )
        logger.info("LLM: Anthropic %s", settings.LLM_MODEL)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=gemini")

        # Note: Gemini 1.5 Flash is recommended for speed/cost
        model = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL if settings.LLM_MODEL != "gpt-4o" else "gemini-1.5-flash",
            temperature=settings.LLM_TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        logger.info("LLM: Gemini %s", model.model)

    elif provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")

        model = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            groq_api_key=settings.GROQ_API_KEY,
        )
        logger.info("LLM: Groq %s", settings.LLM_MODEL)

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. Use 'openai', 'anthropic', 'gemini', or 'groq'."
        )

    return model
