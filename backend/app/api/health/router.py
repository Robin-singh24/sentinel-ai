"""
Health check endpoint for Sentinel AI.

Provides a lightweight liveness signal that confirms:
  - The application process is running.
  - The configuration has been loaded successfully.
  - The API layer is reachable.
  - The database connection pool can reach PostgreSQL.

Route: GET /api/v1/health

Database check strategy:
  The endpoint executes `SELECT 1` directly via the engine (not the session
  factory) to avoid session lifecycle side-effects in a read-only probe.
  If Postgres is unreachable the response still returns HTTP 200 with
  `"database": "degraded"` — the process is alive even if a downstream
  dependency is temporarily unavailable.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.common.responses import SuccessResponse
from app.config.settings import Settings, get_settings
from app.core.logging import get_logger
from app.database.engine import engine

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=SuccessResponse[dict[str, str]],
    summary="Application health check",
    description=(
        "Returns the current operational status of the Sentinel AI backend. "
        "Checks application liveness and database connectivity. "
        "No authentication is required. Use this endpoint for liveness probes."
    ),
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessResponse[dict[str, str]]:
    """
    Return the health status of the application.

    The response includes:
    - **status**: `ok` when the service is running normally.
    - **version**: The currently deployed application version.
    - **environment**: The active deployment environment.
    - **database**: `ok` if PostgreSQL is reachable; `degraded` otherwise.
    """
    logger.debug("Health check requested.")

    database_status = await _check_database_connectivity()

    return SuccessResponse(
        data={
            "status": "ok",
            "version": settings.app_version,
            "environment": settings.environment,
            "database": database_status,
        }
    )


async def _check_database_connectivity() -> str:
    """
    Execute `SELECT 1` against the database to verify pool connectivity.

    Uses the engine directly (not the session dependency) to avoid commit /
    rollback side-effects in a read-only probe. The connection is returned
    to the pool immediately after the check.

    Returns:
        "ok" if the database responds successfully.
        "degraded" if any exception is raised.
    """
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        logger.warning(
            "Database connectivity check failed.",
            extra={"error": str(exc)},
        )
        return "degraded"
