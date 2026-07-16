"""Metadata generator for the ingestion pipeline."""

import hashlib
import time
from uuid import UUID

from app.core.logging import get_logger
from app.modules.ingestion.chunking.models import Chunk
from app.modules.ingestion.metadata.models import ProcessedChunk
from app.modules.ingestion.normalization.models import NormalizedDocument

logger = get_logger(__name__)


class MetadataGenerator:
    """Enriches raw chunks with deterministic IDs, page numbers, and token counts."""

    def generate(
        self,
        document: NormalizedDocument,
        chunks: list[Chunk],
        document_id: UUID,
        workspace_id: UUID,
    ) -> list[ProcessedChunk]:
        """Process chunks and return enriched ProcessedChunk objects."""
        logger.info("Metadata generation started.", extra={"document_id": str(document_id)})
        start_time = time.monotonic()

        if not chunks:
            logger.info("No chunks to process.", extra={"document_id": str(document_id)})
            return []

        processed_chunks = []
        current_offset = 0

        for chunk in chunks:
            # Deterministic SHA-256 chunk ID
            hash_input = f"{document_id}:{chunk.chunk_index}:{chunk.content}"
            chunk_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

            # MVP token approximation: whitespace word count
            token_count = len(chunk.content.split())

            # Page number resolution
            idx = document.normalized_text.find(chunk.content, current_offset)
            if idx != -1:
                page_number = 1 + document.normalized_text.count("\f", 0, idx)
                current_offset = idx + len(chunk.content)
            else:
                page_number = 1

            processed_chunks.append(
                ProcessedChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    workspace_id=workspace_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    character_count=chunk.character_count,
                    token_count=token_count,
                    page_number=page_number,
                )
            )

        logger.info(
            "Metadata generation completed.",
            extra={
                "document_id": str(document_id),
                "chunk_count": len(processed_chunks),
                "duration_ms": round((time.monotonic() - start_time) * 1000),
            },
        )
        return processed_chunks
