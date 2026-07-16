"""
Sentinel AI — FastAPI application entry point.

This module:
  1. Configures structured logging before anything else runs.
  2. Creates the FastAPI application instance via a factory function.
  3. Registers the global exception handler for domain errors.
  4. Mounts the versioned API router.
  5. Manages application lifecycle (startup / shutdown) via a lifespan context.

The application is started by Uvicorn pointing at `app.main:app`.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_v1_router
from app.common.exceptions import SentinelBaseException
from app.common.responses import ErrorDetail, ErrorResponse
from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.engine import engine as db_engine

# ── Bootstrap ─────────────────────────────────────────────────────────────────
# Logging must be configured before the first logger is obtained so that the
# log level from settings is applied to every subsequent logger in the process.
_settings = get_settings()
configure_logging(log_level=_settings.log_level)

logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown events.

    Startup:
        - Log confirmed configuration (no secrets).
        - Future: initialise database connection pools, vector client, etc.

    Shutdown:
        - Log graceful shutdown.
        - Future: close connection pools and flush telemetry.
    """
    settings = get_settings()

    logger.info(
        "Sentinel AI starting.",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "log_level": settings.log_level,
            "postgres_host": settings.postgres_host,
            "postgres_db": settings.postgres_db,
        },
    )

    yield  # Application is now running and accepting requests.

    # ── Shutdown ───────────────────────────────────────────────────────────
    # Dispose the engine — closes all pooled connections cleanly.
    await db_engine.dispose()
    logger.info("Database engine disposed.")
    logger.info("Sentinel AI shutting down gracefully.")


# ── Application factory ────────────────────────────────────────────────────────


def create_application() -> FastAPI:
    """
    Construct and configure the FastAPI application instance.

    Separating construction into a factory function makes the application
    testable — tests can call `create_application()` to obtain a clean instance.

    Returns:
        A fully configured `FastAPI` instance.
    """
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Sentinel AI is an Enterprise Knowledge & Investigation Platform "
            "that enables engineering teams to retrieve organisational knowledge "
            "using AI-powered multi-agent workflows."
        ),
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url="/api/redoc" if settings.environment != "production" else None,
        openapi_url="/api/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Permissive defaults for local development; restrict in production via env.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    _register_exception_handlers(application)

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(api_v1_router)

    return application


def _register_exception_handlers(application: FastAPI) -> None:
    """
    Register global exception handlers on the application instance.

    Domain exceptions (`SentinelBaseException` and its subclasses) are
    translated into structured `ErrorResponse` JSON at a single point,
    keeping individual endpoint handlers free of HTTP conversion logic.
    """

    @application.exception_handler(SentinelBaseException)
    async def sentinel_exception_handler(
        request: Request, exc: SentinelBaseException
    ) -> JSONResponse:
        logger.warning(
            "Domain exception raised.",
            extra={
                "code": exc.code,
                "http_status": exc.http_status,
                "path": str(request.url),
                "message": exc.message,
            },
        )
        error_response = ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message)
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=error_response.model_dump(),
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception.",
            extra={"path": str(request.url), "error": str(exc)},
            exc_info=True,
        )
        error_response = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again later.",
            )
        )
        return JSONResponse(status_code=500, content=error_response.model_dump())


# ── Application instance ───────────────────────────────────────────────────────
app: FastAPI = create_application()
