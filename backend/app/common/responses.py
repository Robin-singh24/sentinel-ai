"""
Standardized API response schemas for Sentinel AI.

Every endpoint must return either `SuccessResponse` or `ErrorResponse` to
guarantee a consistent contract across the entire API surface.

These schemas are generic so that typed responses can be declared in endpoint
signatures, enabling automatic OpenAPI schema generation.

Usage:
    from app.common.responses import SuccessResponse, ErrorResponse

    @router.get("/health", response_model=SuccessResponse[HealthSchema])
    async def health() -> SuccessResponse[HealthSchema]:
        return SuccessResponse(data=HealthSchema(...))
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """
    Envelope for all successful API responses.

    Attributes:
        success: Always True for success responses.
        data:    The response payload.
    """

    success: bool = Field(default=True, description="Indicates a successful response.")
    data: T = Field(description="The response payload.")


class ErrorDetail(BaseModel):
    """
    Machine-readable error detail attached to an ErrorResponse.

    Attributes:
        code:    A short, stable error code string (e.g. 'NOT_FOUND').
        message: A human-readable explanation of the error.
        field:   Optional — the input field that caused the error.
    """

    code: str = Field(description="Short error code.")
    message: str = Field(description="Human-readable error description.")
    field: str | None = Field(default=None, description="Field that caused the error, if any.")


class ErrorResponse(BaseModel):
    """
    Envelope for all error API responses.

    Attributes:
        success: Always False for error responses.
        error:   The structured error detail.
    """

    success: bool = Field(default=False, description="Indicates a failed response.")
    error: ErrorDetail = Field(description="Structured error information.")
