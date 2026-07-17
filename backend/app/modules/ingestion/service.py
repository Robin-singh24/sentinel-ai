"""Orchestrator service for the document ingestion pipeline."""

import time
from typing import Callable

from app.core.logging import get_logger
from app.modules.ingestion.chunking import TextChunker
from app.modules.ingestion.metadata import MetadataGenerator
from app.modules.ingestion.metadata.models import ProcessedChunk
from app.modules.ingestion.models import DocumentProcessingContext
from app.modules.ingestion.normalization import TextNormalizer
from app.modules.ingestion.parsers.base import BaseParser, get_parser

logger = get_logger(__name__)


class DocumentProcessingOrchestrator:
    """Coordinates the document processing pipeline from parsing to metadata generation."""

    def __init__(
        self,
        normalizer: TextNormalizer,
        chunker: TextChunker,
        metadata_generator: MetadataGenerator,
        parser_factory: Callable[[DocumentProcessingContext], BaseParser] = get_parser,
    ) -> None:
        self._normalizer = normalizer
        self._chunker = chunker
        self._metadata_generator = metadata_generator
        self._parser_factory = parser_factory

    def process_document(self, context: DocumentProcessingContext) -> list[ProcessedChunk]:
        """Execute the ingestion pipeline for a given document."""
        logger.info(
            "Document processing pipeline started.",
            extra={
                "document_id": str(context.document_id),
                "filename": context.original_filename,
            },
        )
        start_time = time.monotonic()

        parser = self._parser_factory(context)
        
        logger.info(
            "Selected parser for document.",
            extra={
                "document_id": str(context.document_id),
                "parser": parser.__class__.__name__,
            },
        )

        parsed_doc = parser.parse(context.file_path)
        normalized_doc = self._normalizer.normalize(parsed_doc)
        chunks = self._chunker.chunk(normalized_doc)
        processed_chunks = self._metadata_generator.generate(
            document=normalized_doc,
            chunks=chunks,
            document_id=context.document_id,
            workspace_id=context.workspace_id,
        )

        logger.info(
            "Document processing pipeline completed.",
            extra={
                "document_id": str(context.document_id),
                "chunk_count": len(processed_chunks),
                "duration_ms": round((time.monotonic() - start_time) * 1000),
            },
        )

        return processed_chunks
