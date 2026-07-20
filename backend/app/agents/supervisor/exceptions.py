"""Supervisor-specific exception types."""

from app.common.exceptions import SentinelBaseException


class SentinelSupervisorError(SentinelBaseException):
    """Raised when a supervisor orchestration operation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="SUPERVISOR_ERROR", http_status=500)
