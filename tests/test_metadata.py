"""Unit tests for the metadata generation engine."""

import uuid

from app.modules.ingestion.chunking.models import Chunk
from app.modules.ingestion.metadata import MetadataGenerator
from app.modules.ingestion.normalization.models import NormalizedDocument
from app.modules.ingestion.parsers.base import DocumentType


def _make_doc(text: str) -> NormalizedDocument:
    return NormalizedDocument(
        normalized_text=text,
        original_filename="test.pdf",
        document_type=DocumentType.pdf,
        page_count=3,
    )


def test_empty_chunks():
    """Verify empty chunk lists are handled gracefully."""
    generator = MetadataGenerator()
    result = generator.generate(
        document=_make_doc(""),
        chunks=[],
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
    )
    assert result == []


def test_deterministic_chunk_ids():
    """Verify chunk IDs are deterministic SHA-256 hashes."""
    document_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    chunk = Chunk(chunk_index=0, content="Hello World", character_count=11)

    generator = MetadataGenerator()
    result1 = generator.generate(_make_doc("Hello World"), [chunk], document_id, workspace_id)
    result2 = generator.generate(_make_doc("Hello World"), [chunk], document_id, workspace_id)

    assert len(result1) == 1
    assert result1[0].chunk_id == result2[0].chunk_id
    assert len(result1[0].chunk_id) == 64  # SHA-256 hex digest length
    assert isinstance(result1[0].chunk_id, str)

    # Different content produces different ID
    chunk_diff = Chunk(chunk_index=0, content="Hello Python", character_count=12)
    result3 = generator.generate(_make_doc("Hello Python"), [chunk_diff], document_id, workspace_id)
    assert result3[0].chunk_id != result1[0].chunk_id


def test_token_count_approximation():
    """Verify token count uses whitespace splitting."""
    generator = MetadataGenerator()
    chunk = Chunk(chunk_index=0, content="This is   a test\nstring.", character_count=23)

    result = generator.generate(
        document=_make_doc("This is   a test\nstring."),
        chunks=[chunk],
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
    )

    assert result[0].token_count == 5


def test_page_number_resolution():
    """Verify page numbers are correctly resolved using form-feeds."""
    text = "Page 1 start.\fPage 2 start.\fPage 3 start."
    doc = _make_doc(text)

    chunks = [
        Chunk(chunk_index=0, content="Page 1 start.", character_count=13),
        Chunk(chunk_index=1, content="Page 2 start.", character_count=13),
        Chunk(chunk_index=2, content="Page 3 start.", character_count=13),
    ]

    generator = MetadataGenerator()
    result = generator.generate(
        document=doc,
        chunks=chunks,
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
    )

    assert result[0].page_number == 1
    assert result[1].page_number == 2
    assert result[2].page_number == 3


def test_page_number_with_repeated_content():
    """Verify substring search advances offset correctly for repeated content."""
    text = "Repeated\fRepeated\fRepeated"
    doc = _make_doc(text)

    chunks = [
        Chunk(chunk_index=0, content="Repeated", character_count=8),
        Chunk(chunk_index=1, content="Repeated", character_count=8),
        Chunk(chunk_index=2, content="Repeated", character_count=8),
    ]

    generator = MetadataGenerator()
    result = generator.generate(
        document=doc,
        chunks=chunks,
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
    )

    assert result[0].page_number == 1
    assert result[1].page_number == 2
    assert result[2].page_number == 3


def test_metadata_passthrough():
    """Verify that indices, character counts, and foreign keys are preserved."""
    document_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    chunk = Chunk(chunk_index=42, content="Data", character_count=4)

    generator = MetadataGenerator()
    result = generator.generate(
        document=_make_doc("Data"),
        chunks=[chunk],
        document_id=document_id,
        workspace_id=workspace_id,
    )

    assert result[0].document_id == document_id
    assert result[0].workspace_id == workspace_id
    assert result[0].chunk_index == 42
    assert result[0].character_count == 4
    assert result[0].content == "Data"
