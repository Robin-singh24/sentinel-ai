"""
Health check endpoint for Sentinel AI.

Provides a lightweight liveness signal that confirms:
  - The application process is running.
  - The configuration has been loaded successfully.
  - The API layer is reachable.

Route: GET /api/v1/health
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.common.responses import SuccessResponse
from app.config.settings import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


class HealthStatus:
    """Holds the fields returned by the health endpoint."""

    __slots__ = ("status", "version", "environment")

    def __init__(self, status: str, version: str, environment: str) -> None:
        self.status = status
        self.version = version
        self.environment = environment


class HealthResponse(SuccessResponse[dict[str, str]]):
    """Typed response model for the health endpoint."""


@router.get(
    "/health",
    response_model=SuccessResponse[dict[str, str]],
    summary="Application health check",
    description=(
        "Returns the current operational status of the Sentinel AI backend. "
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
    """
    logger.debug("Health check requested.")

    return SuccessResponse(
        data={
            "status": "ok",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    )
