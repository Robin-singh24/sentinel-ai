"""Unit tests for the document processing orchestrator."""

import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.modules.ingestion.chunking import TextChunker
from app.modules.ingestion.chunking.models import Chunk
from app.modules.ingestion.metadata import MetadataGenerator
from app.modules.ingestion.metadata.models import ProcessedChunk
from app.modules.ingestion.models import DocumentProcessingContext
from app.modules.ingestion.normalization import TextNormalizer
from app.modules.ingestion.normalization.models import NormalizedDocument
from app.modules.ingestion.parsers.base import BaseParser, DocumentType, ParsedDocument
from app.modules.ingestion.parsers.exceptions import ParseEmptyDocumentError
from app.modules.ingestion.service import DocumentProcessingOrchestrator


@pytest.fixture
def dummy_context() -> DocumentProcessingContext:
    return DocumentProcessingContext(
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        file_path=Path("/tmp/test.pdf"),
        original_filename="test.pdf",
        mime_type="application/pdf",
    )


@pytest.fixture
def mock_parser():
    parser = Mock(spec=BaseParser)
    parser.parse.return_value = ParsedDocument(
        text="raw text",
        original_filename="test.pdf",
        document_type=DocumentType.pdf,
        page_count=1,
    )
    return parser


@pytest.fixture
def mock_normalizer():
    normalizer = Mock(spec=TextNormalizer)
    normalizer.normalize.return_value = NormalizedDocument(
        normalized_text="normalized text",
        original_filename="test.pdf",
        document_type=DocumentType.pdf,
        page_count=1,
    )
    return normalizer


@pytest.fixture
def mock_chunker():
    chunker = Mock(spec=TextChunker)
    chunker.chunk.return_value = [
        Chunk(chunk_index=0, content="chunk1", character_count=6)
    ]
    return chunker


@pytest.fixture
def mock_metadata_generator():
    generator = Mock(spec=MetadataGenerator)
    generator.generate.return_value = [
        ProcessedChunk(
            chunk_id="hash",
            document_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            chunk_index=0,
            content="chunk1",
            character_count=6,
            token_count=1,
            page_number=1,
        )
    ]
    return generator


def test_successful_processing_pipeline(
    dummy_context, mock_parser, mock_normalizer, mock_chunker, mock_metadata_generator
):
    """Verify the orchestrator calls components in the correct order."""

    def parser_factory(context):
        return mock_parser

    orchestrator = DocumentProcessingOrchestrator(
        normalizer=mock_normalizer,
        chunker=mock_chunker,
        metadata_generator=mock_metadata_generator,
        parser_factory=parser_factory,
    )

    result = orchestrator.process_document(dummy_context)

    assert len(result) == 1
    assert isinstance(result[0], ProcessedChunk)

    mock_parser.parse.assert_called_once_with(dummy_context.file_path)
    mock_normalizer.normalize.assert_called_once_with(mock_parser.parse.return_value)
    mock_chunker.chunk.assert_called_once_with(mock_normalizer.normalize.return_value)
    mock_metadata_generator.generate.assert_called_once_with(
        document=mock_normalizer.normalize.return_value,
        chunks=mock_chunker.chunk.return_value,
        document_id=dummy_context.document_id,
        workspace_id=dummy_context.workspace_id,
    )


def test_parser_failure_aborts_pipeline(
    dummy_context, mock_parser, mock_normalizer, mock_chunker, mock_metadata_generator
):
    """Verify that an exception in the parser halts execution and bubbles up."""
    mock_parser.parse.side_effect = RuntimeError("Parser failed")

    def parser_factory(context):
        return mock_parser

    orchestrator = DocumentProcessingOrchestrator(
        normalizer=mock_normalizer,
        chunker=mock_chunker,
        metadata_generator=mock_metadata_generator,
        parser_factory=parser_factory,
    )

    with pytest.raises(RuntimeError, match="Parser failed"):
        orchestrator.process_document(dummy_context)

    mock_normalizer.normalize.assert_not_called()
    mock_chunker.chunk.assert_not_called()
    mock_metadata_generator.generate.assert_not_called()


def test_normalizer_failure_aborts_pipeline(
    dummy_context, mock_parser, mock_normalizer, mock_chunker, mock_metadata_generator
):
    """Verify that an exception in the normalizer halts execution (e.g. empty document)."""
    mock_normalizer.normalize.side_effect = ParseEmptyDocumentError("test.pdf")

    orchestrator = DocumentProcessingOrchestrator(
        normalizer=mock_normalizer,
        chunker=mock_chunker,
        metadata_generator=mock_metadata_generator,
        parser_factory=lambda _: mock_parser,
    )

    with pytest.raises(ParseEmptyDocumentError):
        orchestrator.process_document(dummy_context)

    mock_parser.parse.assert_called_once()
    mock_chunker.chunk.assert_not_called()
    mock_metadata_generator.generate.assert_not_called()


def test_chunker_failure_aborts_pipeline(
    dummy_context, mock_parser, mock_normalizer, mock_chunker, mock_metadata_generator
):
    """Verify chunker exception aborts pipeline."""
    mock_chunker.chunk.side_effect = ValueError("Chunker failed")

    orchestrator = DocumentProcessingOrchestrator(
        normalizer=mock_normalizer,
        chunker=mock_chunker,
        metadata_generator=mock_metadata_generator,
        parser_factory=lambda _: mock_parser,
    )

    with pytest.raises(ValueError):
        orchestrator.process_document(dummy_context)

    mock_normalizer.normalize.assert_called_once()
    mock_metadata_generator.generate.assert_not_called()


def test_empty_chunk_collection(
    dummy_context, mock_parser, mock_normalizer, mock_chunker, mock_metadata_generator
):
    """Verify pipeline continues and returns an empty list if chunker yields no chunks."""
    mock_chunker.chunk.return_value = []
    mock_metadata_generator.generate.return_value = []

    orchestrator = DocumentProcessingOrchestrator(
        normalizer=mock_normalizer,
        chunker=mock_chunker,
        metadata_generator=mock_metadata_generator,
        parser_factory=lambda _: mock_parser,
    )

    result = orchestrator.process_document(dummy_context)

    assert result == []
    mock_metadata_generator.generate.assert_called_once_with(
        document=mock_normalizer.normalize.return_value,
        chunks=[],
        document_id=dummy_context.document_id,
        workspace_id=dummy_context.workspace_id,
    )
