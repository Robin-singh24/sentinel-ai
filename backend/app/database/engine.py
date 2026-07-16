"""
SQLAlchemy async engine for Sentinel AI.

The engine manages the connection pool and is the lowest-level database
primitive. A single engine instance is shared across the entire application
lifecycle — it is created once at startup and disposed on shutdown.

Design decisions:
  - `pool_pre_ping=True`: validates connections before use, preventing errors
    caused by stale connections that were silently dropped by the server.
  - `pool_size` / `max_overflow` / `pool_timeout` / `pool_recycle` are all
    driven from Settings so they can be tuned per environment without code
    changes.
  - The engine is lazy: `create_async_engine` does NOT open connections until
    the first query, so importing this module is safe even if Postgres is down.

Usage:
    from app.database.engine import engine
"""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config.settings import get_settings


def build_engine() -> AsyncEngine:
    """
    Construct an `AsyncEngine` using the current application settings.

    Separated into its own function so tests can call it with custom settings
    without relying on the module-level singleton.

    Returns:
        A configured `AsyncEngine` instance.
    """
    settings = get_settings()

    return create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,
    )


# ── Module-level singleton ────────────────────────────────────────────────────
# One engine instance per process — shared by the session factory and the
# health check. Disposed explicitly in main.py's lifespan shutdown hook.
engine: AsyncEngine = build_engine()
