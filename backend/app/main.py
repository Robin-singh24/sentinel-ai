import sys
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
from app.database import models as _models
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.exceptions import SentinelVectorStoreError


_settings = get_settings()
configure_logging(log_level=_settings.log_level)

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:

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

    qdrant_manager = QdrantConnectionManager(settings=settings)
    application.state.qdrant_manager = qdrant_manager
    try:
        await qdrant_manager.check_health()
    except SentinelVectorStoreError as e:
        logger.critical(
            "Vector store infrastructure initialization failed.",
            extra={"error": e.message}
        )
        sys.exit(1)

    yield 

    await qdrant_manager.close()
    await db_engine.dispose()
    logger.info("Database engine disposed.")
    logger.info("Sentinel AI shutting down gracefully.")

def create_application() -> FastAPI:
    
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

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(application)
    
    application.include_router(api_v1_router)

    return application


def _register_exception_handlers(application: FastAPI) -> None:
    
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
                "error_message": exc.message,
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


app: FastAPI = create_application()
