"""
Structured logging configuration for Sentinel AI.

Produces JSON-formatted log records on stdout. Each record includes:
  - timestamp
  - level
  - name  (module / logger name)
  - message
  - request_id  (when populated on the log record)

Sensitive fields (tokens, passwords, secrets) must never be logged.

Usage:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Workspace created", extra={"workspace_id": workspace_id})
"""

import logging
import sys

from pythonjsonlogger.json import JsonFormatter


def _build_formatter() -> JsonFormatter:
    """
    Return a JSON formatter that emits a consistent set of fields.

    The format string lists the fields to include in every record.
    Additional fields can be injected via the `extra` dict on each log call.
    """
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    return JsonFormatter(fmt=fmt, rename_fields={"asctime": "timestamp", "levelname": "level"})


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure the root logger for the entire application.

    This function is called once during application startup. All subsequent
    calls to `get_logger` will inherit this configuration automatically.

    Args:
        log_level: One of DEBUG | INFO | WARNING | ERROR | CRITICAL.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_build_formatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any default handlers that may have been registered before this call
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers that are not useful in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Args:
        name: Typically `__name__` of the calling module.

    Returns:
        A standard `logging.Logger` instance.
    """
    return logging.getLogger(name)
