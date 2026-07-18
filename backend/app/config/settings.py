"""Application settings — single source of truth for all configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Sentinel AI application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application 
    app_name: str = "Sentinel AI"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging 
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # PostgreSQL — individual credentials
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "sentinel"
    postgres_user: str = "sentinel"
    postgres_password: str = "sentinel"

    # Database connection pool 
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30        
    db_pool_recycle: int = 1800      
    db_echo: bool = False            

    # Redis 
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_https: bool = False
    qdrant_timeout: int = 10

    # LLM Provider 
    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    groq_api_key: str = ""

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # File upload
    upload_directory: str = "/app/uploads"
    max_upload_size_mb: int = 25

    # Document Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Embedding Provider
    embedding_provider: str = "bge_m3"
    embedding_model: str = "BAAI/bge-m3"
    embedding_batch_size: int = 32

    # Computed fields

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy DSN assembled from individual Postgres credentials."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def qdrant_url(self) -> str:
        """Qdrant connection URL assembled from host, port, and scheme."""
        scheme = "https" if self.qdrant_https else "http"
        return f"{scheme}://{self.qdrant_host}:{self.qdrant_port}"


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
