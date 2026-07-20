"""Retrieval-specific exception types."""

from app.common.exceptions import SentinelBaseException


class SentinelRetrievalError(SentinelBaseException):
    """Raised when a retrieval operation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="RETRIEVAL_ERROR", http_status=500)
