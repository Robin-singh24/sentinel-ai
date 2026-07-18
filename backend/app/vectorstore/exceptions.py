"""
Exceptions for the vector store module.
"""

from app.common.exceptions import SentinelBaseException


class SentinelVectorStoreError(SentinelBaseException):
    """
    Raised when a vector store infrastructure operation fails
    (e.g., connection timeout, missing collections).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="VECTOR_STORE_ERROR", http_status=500)
