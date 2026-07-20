"""Exceptions for the response agent."""

from app.common.exceptions import SentinelBaseException


class SentinelResponseError(SentinelBaseException):
    """Exception raised for errors during response generation."""

    def __init__(
        self,
        message: str,
        code: str = "RESPONSE_GENERATION_ERROR",
        http_status: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, http_status=http_status)
