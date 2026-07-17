from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.modules.ingestion.models import DocumentProcessingContext
from app.modules.ingestion.parsers.exceptions import ParseUnsupportedTypeError


class DocumentType(str, enum.Enum):
    """Canonical document type identifiers used throughout the ingestion pipeline."""

    pdf = "pdf"
    markdown = "markdown"
    text = "text"


@dataclass(frozen=True)
class ParsedDocument:
    """Structured output produced by every parser."""

    text: str
    original_filename: str
    document_type: DocumentType
    page_count: int


class BaseParser(ABC):
    """Abstract base class for all document parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """Extract raw text from the file at *file_path*."""


# MIME type and extension maps
_MIME_TO_TYPE: dict[str, DocumentType] = {
    "application/pdf": DocumentType.pdf,
    "text/markdown": DocumentType.markdown,
    "text/x-markdown": DocumentType.markdown,
    "text/plain": DocumentType.text,
}

# Fallback lookup when MIME type is absent or generic.
_EXTENSION_TO_TYPE: dict[str, DocumentType] = {
    ".pdf": DocumentType.pdf,
    ".md": DocumentType.markdown,
    ".markdown": DocumentType.markdown,
    ".txt": DocumentType.text,
}


def get_parser(context: DocumentProcessingContext) -> BaseParser:
    """Return the correct parser instance for the given file context."""
    from app.modules.ingestion.parsers.markdown_parser import MarkdownParser
    from app.modules.ingestion.parsers.pdf_parser import PdfParser
    from app.modules.ingestion.parsers.text_parser import TextParser

    _TYPE_TO_PARSER: dict[DocumentType, BaseParser] = {
        DocumentType.pdf: PdfParser(),
        DocumentType.markdown: MarkdownParser(),
        DocumentType.text: TextParser(),
    }

    doc_type = _MIME_TO_TYPE.get(context.mime_type.lower())

    if doc_type is None:
        extension = Path(context.original_filename).suffix.lower()
        doc_type = _EXTENSION_TO_TYPE.get(extension)

    if doc_type is None:
        raise ParseUnsupportedTypeError(mime_type=context.mime_type)

    return _TYPE_TO_PARSER[doc_type]
