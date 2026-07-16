"""PDF parser — extracts text from PDF files using PyMuPDF."""

import time
from pathlib import Path

import fitz  # PyMuPDF

from app.core.logging import get_logger
from app.modules.ingestion.parsers.base import BaseParser, DocumentType, ParsedDocument
from app.modules.ingestion.parsers.exceptions import (
    ParseCorruptedFileError,
    ParseEmptyDocumentError,
)

logger = get_logger(__name__)


class PdfParser(BaseParser):
    """Extracts plain text from PDF documents page-by-page using PyMuPDF."""

    def parse(self, file_path: Path) -> ParsedDocument:
        """Extract all text from a PDF, preserving page order."""
        filename = file_path.name
        start = time.monotonic()

        try:
            doc = fitz.open(str(file_path))
        except Exception as exc:
            raise ParseCorruptedFileError(filename=filename, reason=str(exc)) from exc

        try:
            page_count = len(doc)
            pages: list[str] = []

            for page in doc:
                pages.append(page.get_text())
        finally:
            doc.close()

        # Form-feed preserves the page boundary signal for later pipeline stages.
        text = "\f".join(pages)

        logger.info(
            "PDF parsed.",
            extra={
                "filename": filename,
                "page_count": page_count,
                "duration_ms": round((time.monotonic() - start) * 1000),
                "parser": "PdfParser",
            },
        )

        if not text.strip():
            raise ParseEmptyDocumentError(filename=filename)

        return ParsedDocument(
            text=text,
            original_filename=filename,
            document_type=DocumentType.pdf,
            page_count=page_count,
        )
