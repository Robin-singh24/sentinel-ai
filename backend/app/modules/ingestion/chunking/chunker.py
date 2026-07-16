"""Chunking engine for the ingestion pipeline."""

import time

from app.common.exceptions import SentinelValidationError
from app.core.logging import get_logger
from app.modules.ingestion.chunking.models import Chunk
from app.modules.ingestion.normalization.models import NormalizedDocument

logger = get_logger(__name__)


class TextChunker:
    """Divides normalized text into overlapping chunks using semantic boundaries. """

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise SentinelValidationError(message="chunk_size must be greater than 0.")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise SentinelValidationError(
                message="chunk_overlap must be non-negative and less than chunk_size."
            )

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = ["\f", "\n\n", "\n", " "]

    def chunk(self, document: NormalizedDocument) -> list[Chunk]:
        """Split a NormalizedDocument into an ordered list of Chunks."""
        logger.info(
            "Chunking started.",
            extra={"filename": document.original_filename},
        )
        start_time = time.monotonic()

        text = document.normalized_text
        chunks: list[Chunk] = []

        if not text.strip():
            logger.info(
                "Chunking skipped for empty document.",
                extra={"filename": document.original_filename},
            )
            return chunks

        start = 0
        chunk_index = 0

        while start < len(text):
            if len(text) - start <= self._chunk_size:
                chunk_content = text[start:].strip()
                if chunk_content:
                    chunks.append(
                        Chunk(
                            chunk_index=chunk_index,
                            content=chunk_content,
                            character_count=len(chunk_content),
                        )
                    )
                break

            window = text[start : start + self._chunk_size]
            split_offset = -1

            for sep in self._separators:
                idx = window.rfind(sep)
                if idx > 0:  # Must advance forward
                    split_offset = idx + len(sep)
                    break

            if split_offset == -1:
                split_offset = self._chunk_size

            current_end = start + split_offset
            chunk_content = text[start:current_end].strip()

            if chunk_content:
                chunks.append(
                    Chunk(
                        chunk_index=chunk_index,
                        content=chunk_content,
                        character_count=len(chunk_content),
                    )
                )
                chunk_index += 1

            target_start = current_end - self._chunk_overlap
            if target_start <= start:
                target_start = start + 1

            overlap_window = text[target_start:current_end]
            overlap_offset = -1

            for sep in self._separators:
                idx = overlap_window.find(sep)
                if idx != -1:
                    overlap_offset = idx + len(sep)
                    break

            if overlap_offset != -1:
                next_start = target_start + overlap_offset
            else:
                next_start = target_start

            if next_start <= start:
                next_start = start + 1

            start = next_start

        logger.info(
            "Chunking completed.",
            extra={
                "filename": document.original_filename,
                "chunk_count": len(chunks),
                "duration_ms": round((time.monotonic() - start_time) * 1000),
            },
        )
        return chunks
