"""
Application settings — single source of truth for all configuration.

All values are loaded exclusively from environment variables (or a .env file
in development). No secret or environment-specific value is ever hardcoded.

Usage:
    from app.config.settings import get_settings

    settings = get_settings()
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Sentinel AI application settings.

    Reads from environment variables. Variable names are case-insensitive.
    A `.env` file in the project root is automatically loaded when present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "Sentinel AI"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # ── Server ───────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── Database (future — not connected yet) ────────────────────────────────
    database_url: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"

    # ── Redis (future — not connected yet) ───────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Qdrant (future — not connected yet) ──────────────────────────────────
    qdrant_url: str = "http://localhost:6333"

    # ── LLM Provider (future — not used yet) ─────────────────────────────────
    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    groq_api_key: str = ""

    # ── JWT (future — not used yet) ───────────────────────────────────────────
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Using @lru_cache ensures the .env file is parsed exactly once per process.
    This function is the canonical Dependency Injection provider for settings.

    Example:
        # In a FastAPI endpoint:
        def my_route(settings: Annotated[Settings, Depends(get_settings)]):
            ...
    """
    return Settings()
