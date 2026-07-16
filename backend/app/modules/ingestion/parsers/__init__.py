"""Public API for the parsers sub-package.

Callers outside the ingestion module should import from here rather than
from the individual parser modules directly. This insulates consumers from
internal restructuring.

    from app.modules.ingestion.parsers import get_parser, ParsedDocument
"""

from app.modules.ingestion.parsers.base import BaseParser, DocumentType, ParsedDocument, get_parser
from app.modules.ingestion.parsers.exceptions import (
    ParseCorruptedFileError,
    ParseEmptyDocumentError,
    ParseUnsupportedTypeError,
)

__all__ = [
    "BaseParser",
    "DocumentType",
    "ParsedDocument",
    "get_parser",
    "ParseCorruptedFileError",
    "ParseEmptyDocumentError",
    "ParseUnsupportedTypeError",
]
