"""
Domain exception hierarchy for Sentinel AI.

All application-level errors must inherit from `SentinelBaseException`.
This allows exception handlers registered in `main.py` to intercept every
domain error at a single point and convert it to a consistent HTTP response.

Error categories (aligned with LLD §11):
  - Validation errors       → HTTP 422
  - Not found errors        → HTTP 404
  - Internal server errors  → HTTP 500

Usage:
    from app.common.exceptions import SentinelNotFoundError

    raise SentinelNotFoundError(resource="workspace", identifier=workspace_id)
"""


class SentinelBaseException(Exception):
    """
    Base class for all Sentinel AI domain exceptions.

    Attributes:
        message:     Human-readable description of what went wrong.
        code:        Short, stable error code string.
        http_status: HTTP status code to return to the client.
    """

    message: str
    code: str
    http_status: int

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", http_status: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status


class SentinelNotFoundError(SentinelBaseException):
    """
    Raised when a requested resource cannot be located.

    Args:
        resource:   The type of resource that was not found (e.g. "workspace").
        identifier: The ID or key that was looked up.
    """

    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="NOT_FOUND",
            http_status=404,
        )


class SentinelValidationError(SentinelBaseException):
    """
    Raised when an input fails domain-level validation rules.

    Args:
        message: A human-readable explanation of the validation failure.
        field:   Optional — the specific input field that is invalid.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        detail = f"[{field}] {message}" if field else message
        super().__init__(
            message=detail,
            code="VALIDATION_ERROR",
            http_status=422,
        )
        self.field = field


class SentinelUnauthorizedError(SentinelBaseException):
    """Raised when a user cannot be authenticated."""

    def __init__(self, message: str = "Authentication is required.") -> None:
        super().__init__(message=message, code="UNAUTHORIZED", http_status=401)


class SentinelForbiddenError(SentinelBaseException):
    """Raised when an authenticated user lacks permission for the requested action."""

    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(message=message, code="FORBIDDEN", http_status=403)
