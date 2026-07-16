"""Parse-specific domain exceptions for the ingestion pipeline."""

from app.common.exceptions import SentinelBaseException


class ParseUnsupportedTypeError(SentinelBaseException):
    """Raised when no parser exists for the supplied MIME type or file extension."""

    def __init__(self, mime_type: str) -> None:
        super().__init__(
            message=f"No parser available for document type '{mime_type}'.",
            code="PARSE_UNSUPPORTED_TYPE",
            http_status=422,
        )


class ParseCorruptedFileError(SentinelBaseException):
    """Raised when a file cannot be opened or decoded by its designated parser."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to parse '{filename}': {reason}",
            code="PARSE_CORRUPTED_FILE",
            http_status=422,
        )


class ParseEmptyDocumentError(SentinelBaseException):
    """Raised when the parser extracts no usable text from a document."""

    def __init__(self, filename: str) -> None:
        super().__init__(
            message=f"Document '{filename}' contains no extractable text.",
            code="PARSE_EMPTY_DOCUMENT",
            http_status=422,
        )
