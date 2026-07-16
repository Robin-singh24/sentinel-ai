"""Storage-specific domain exceptions."""

from app.common.exceptions import SentinelBaseException


class StorageWriteError(SentinelBaseException):
    """Raised when a file cannot be written to the configured storage location."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to write file '{path}': {reason}",
            code="STORAGE_WRITE_ERROR",
            http_status=500,
        )


class StorageDeleteError(SentinelBaseException):
    """Raised when a file cannot be removed from the configured storage location."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to delete file '{path}': {reason}",
            code="STORAGE_DELETE_ERROR",
            http_status=500,
        )
