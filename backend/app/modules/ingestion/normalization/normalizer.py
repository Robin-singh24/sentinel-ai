"""Text normalization for the ingestion pipeline."""

import re
import time
import unicodedata

from app.core.logging import get_logger
from app.modules.ingestion.normalization.models import NormalizedDocument
from app.modules.ingestion.parsers.base import ParsedDocument
from app.modules.ingestion.parsers.exceptions import ParseEmptyDocumentError

logger = get_logger(__name__)

# Matches any control character except newline, tab, and form-feed.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")

# Collapses 2+ consecutive spaces that are NOT at the start of a line,
_INLINE_SPACES = re.compile(r"(?<=\S) {2,}")

# Three or more consecutive blank lines (lines containing only whitespace).
_EXCESS_BLANK_LINES = re.compile(r"(\n[ \t]*){3,}\n")


class TextNormalizer:
    """Applies a deterministic normalization pipeline to a ParsedDocument."""

    def normalize(self, document: ParsedDocument) -> NormalizedDocument:
        """Normalize *document* and return a NormalizedDocument."""
        logger.info(
            "Normalization started.",
            extra={"filename": document.original_filename},
        )
        start = time.monotonic()

        text = self._apply(document.text, document.original_filename)

        logger.info(
            "Normalization completed.",
            extra={
                "filename": document.original_filename,
                "duration_ms": round((time.monotonic() - start) * 1000),
                "chars_in": len(document.text),
                "chars_out": len(text),
            },
        )

        return NormalizedDocument(
            normalized_text=text,
            original_filename=document.original_filename,
            document_type=document.document_type,
            page_count=document.page_count,
        )

    def _apply(self, text: str, filename: str) -> str:
        """Run all normalization steps in a fixed, documented order."""
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        text = _INLINE_SPACES.sub(" ", text)
        text = _EXCESS_BLANK_LINES.sub("\n\n\n", text)
        text = _CONTROL_CHARS.sub("", text)
        text = text.strip()

        if not text:
            raise ParseEmptyDocumentError(filename=filename)

        return text
