"""Markdown parser — reads raw Markdown text from .md files."""

import time
from pathlib import Path

from app.core.logging import get_logger
from app.modules.ingestion.parsers.base import BaseParser, DocumentType, ParsedDocument
from app.modules.ingestion.parsers.exceptions import (
    ParseCorruptedFileError,
    ParseEmptyDocumentError,
)

logger = get_logger(__name__)


class MarkdownParser(BaseParser):
    """Returns the raw Markdown source of a document without any conversion."""

    def parse(self, file_path: Path) -> ParsedDocument:
        """Read a UTF-8 Markdown file and return its raw text."""
        filename = file_path.name
        start = time.monotonic()

        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ParseCorruptedFileError(filename=filename, reason=str(exc)) from exc

        logger.info(
            "Markdown parsed.",
            extra={
                "filename": filename,
                "duration_ms": round((time.monotonic() - start) * 1000),
                "parser": "MarkdownParser",
            },
        )

        if not text.strip():
            raise ParseEmptyDocumentError(filename=filename)

        return ParsedDocument(
            text=text,
            original_filename=filename,
            document_type=DocumentType.markdown,
            page_count=1,
        )
