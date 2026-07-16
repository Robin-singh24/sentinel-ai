"""Plain-text parser — reads UTF-8 .txt files preserving all whitespace."""

import time
from pathlib import Path

from app.core.logging import get_logger
from app.modules.ingestion.parsers.base import BaseParser, DocumentType, ParsedDocument
from app.modules.ingestion.parsers.exceptions import (
    ParseCorruptedFileError,
    ParseEmptyDocumentError,
)

logger = get_logger(__name__)


class TextParser(BaseParser):
    """Reads plain-text files preserving line breaks and paragraph boundaries."""

    def parse(self, file_path: Path) -> ParsedDocument:
        """Read a UTF-8 plain-text file and return its full contents."""
        filename = file_path.name
        start = time.monotonic()

        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ParseCorruptedFileError(filename=filename, reason=str(exc)) from exc

        logger.info(
            "Text file parsed.",
            extra={
                "filename": filename,
                "duration_ms": round((time.monotonic() - start) * 1000),
                "parser": "TextParser",
            },
        )

        if not text.strip():
            raise ParseEmptyDocumentError(filename=filename)

        return ParsedDocument(
            text=text,
            original_filename=filename,
            document_type=DocumentType.text,
            page_count=1,
        )
