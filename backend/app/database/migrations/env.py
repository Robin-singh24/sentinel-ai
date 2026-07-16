"""
Alembic migration environment for Sentinel AI.

This file is executed by Alembic whenever `alembic upgrade`, `alembic downgrade`,
or `alembic revision --autogenerate` is run.

Key responsibilities:
  - Load the database URL from application settings (not alembic.ini).
  - Import all ORM models so their metadata is visible to --autogenerate.
  - Support both offline mode (SQL script generation) and online mode
    (direct async connection to the live database).

Async driver strategy:
  SQLAlchemy's async engine uses asyncpg. Alembic's migration runner is
  synchronous, so online mode wraps the async connection using
  `connection.run_sync(do_run_migrations)` — the recommended pattern from
  the SQLAlchemy async documentation.

Running migrations:
    # From d:\\Projects\\Sentinel AI\\backend\\
    uv run alembic upgrade head
    uv run alembic revision --autogenerate -m "describe change"
    uv run alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Configure Python logging from alembic.ini if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import application settings ───────────────────────────────────────────────
# `prepend_sys_path = .` in alembic.ini ensures the `backend/` directory is on
# sys.path, so `from app.*` imports work correctly here.
from app.config.settings import get_settings  # noqa: E402

# ── Import ORM Base and all models ────────────────────────────────────────────
# Base.metadata must include every table for --autogenerate to work correctly.
# As domain models are created in future phases, import them here:
#
#   from app.modules.auth.models import User          # noqa: F401
#   from app.modules.workspace.models import Workspace  # noqa: F401
#
from app.database.base import Base  # noqa: E402

target_metadata = Base.metadata


# ── Migration runners ─────────────────────────────────────────────────────────


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode — generates SQL without a live connection.

    Useful for reviewing migration SQL before applying it, or for environments
    where direct DB access is restricted (e.g., production change management).
    """
    settings = get_settings()

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """
    Execute pending migrations against an open synchronous connection.

    Called via `connection.run_sync()` from within the async context so that
    Alembic's synchronous migration runner works with our async engine.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Open an async connection and delegate to the synchronous migration runner.

    Uses `NullPool` to avoid holding idle connections open after the migration
    command completes — migrations are short-lived CLI operations.
    """
    settings = get_settings()

    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (live database) migration execution."""
    asyncio.run(run_async_migrations())


# ── Dispatch ──────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
