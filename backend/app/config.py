"""
Application configuration.

Loads all settings from environment variables with sensible defaults.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised application settings loaded from `.env` or the environment."""

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "Drive Search Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "*"

    # ── LLM Provider ─────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["openai", "anthropic", "gemini", "groq"] = "groq"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048

    # ── Google Drive ─────────────────────────────────────────────────────
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account.json"
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    DRIVE_PAGE_SIZE: int = 20
    DRIVE_MAX_RESULTS: int = 50

    # ── Memory ───────────────────────────────────────────────────────────
    MAX_CONVERSATION_HISTORY: int = 20

    # ── Server ───────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
