"""End-to-End integration tests for the ingestion pipeline."""

import uuid
from pathlib import Path

import fitz
import pytest

from app.modules.ingestion import DocumentProcessingContext, DocumentProcessingOrchestrator
from app.modules.ingestion.chunking import TextChunker
from app.modules.ingestion.metadata import MetadataGenerator
from app.modules.ingestion.normalization import TextNormalizer
from app.modules.ingestion.parsers.base import get_parser
from app.modules.ingestion.parsers.exceptions import (
    ParseEmptyDocumentError,
    ParseUnsupportedTypeError,
)

@pytest.fixture
def orchestrator() -> DocumentProcessingOrchestrator:
    """Provides a real orchestrator instance configured with defaults."""
    return DocumentProcessingOrchestrator(
        normalizer=TextNormalizer(),
        chunker=TextChunker(chunk_size=100, chunk_overlap=20),
        metadata_generator=MetadataGenerator(),
        parser_factory=get_parser,
    )


def test_markdown_end_to_end(tmp_path: Path, orchestrator: DocumentProcessingOrchestrator):
    """Verify complete processing of a Markdown document with normalization and chunking."""
    file_path = tmp_path / "test.md"
    markdown_content = (
        "# Main Heading\n\n"
        "This is a paragraph with some **bold** text and     messy    spaces.\n\n"
        "## Sub Heading\n\n"
        "- Item 1\n"
        "- Item 2\n\n"
        "End of document."
    )
    file_path.write_text(markdown_content, encoding="utf-8")

    doc_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    context = DocumentProcessingContext(
        document_id=doc_id,
        workspace_id=workspace_id,
        file_path=file_path,
        original_filename="test.md",
        mime_type="text/markdown",
    )

    chunks = orchestrator.process_document(context)

    assert len(chunks) > 0
    assert chunks[0].document_id == doc_id
    assert chunks[0].workspace_id == workspace_id
    assert chunks[0].page_number == 1
    
    # Verify normalization worked (messy spaces collapsed)
    full_content = "".join(c.content for c in chunks)
    assert "messy spaces" in full_content
    assert "    " not in full_content


def test_pdf_end_to_end(tmp_path: Path, orchestrator: DocumentProcessingOrchestrator):
    """Verify processing of a PDF document."""
    file_path = tmp_path / "test.pdf"
    
    # Dynamically generate a valid PDF using PyMuPDF (fitz)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), "Hello World")
    doc.save(str(file_path))
    doc.close()

    doc_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    context = DocumentProcessingContext(
        document_id=doc_id,
        workspace_id=workspace_id,
        file_path=file_path,
        original_filename="test.pdf",
        mime_type="application/pdf",
    )

    chunks = orchestrator.process_document(context)

    assert len(chunks) == 1
    assert "Hello" in chunks[0].content


def test_plain_text_overlap_and_ordering(tmp_path: Path, orchestrator: DocumentProcessingOrchestrator):
    """Verify chunk ordering and overlapping on a long plain text document."""
    file_path = tmp_path / "test.txt"
    # Create a doc that is definitely larger than 100 characters (the chunk_size fixture)
    words = [f"word_{i}" for i in range(100)]
    file_path.write_text(" ".join(words), encoding="utf-8")

    context = DocumentProcessingContext(
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        file_path=file_path,
        original_filename="test.txt",
        mime_type="text/plain",
    )

    chunks = orchestrator.process_document(context)

    assert len(chunks) > 1
    # Check deterministic ordering
    assert all(chunks[i].chunk_index == i for i in range(len(chunks)))
    
    # Check overlap (the end of chunk N should appear near the start of chunk N+1)
    for i in range(len(chunks) - 1):
        c1 = chunks[i].content
        c2 = chunks[i+1].content
        # Extract the last few words of c1 and ensure they exist in c2
        # Since overlap is 20 chars, 2 words (e.g., 'word_11 word_12') fit within 20 chars.
        tail_words = c1.split()[-2:]
        overlap_str = " ".join(tail_words)
        assert overlap_str in c2


def test_metadata_determinism(tmp_path: Path, orchestrator: DocumentProcessingOrchestrator):
    """Verify that processing the identical document twice yields identical ProcessedChunks."""
    file_path = tmp_path / "test.md"
    file_path.write_text("Deterministic content is deterministic.", encoding="utf-8")

    doc_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    context = DocumentProcessingContext(
        document_id=doc_id,
        workspace_id=workspace_id,
        file_path=file_path,
        original_filename="test.md",
        mime_type="text/markdown",
    )

    run1 = orchestrator.process_document(context)
    run2 = orchestrator.process_document(context)

    assert len(run1) == len(run2) == 1
    assert run1[0].chunk_id == run2[0].chunk_id
    assert run1[0].content == run2[0].content
    assert run1[0].token_count == run2[0].token_count


def test_unsupported_file_type(tmp_path: Path, orchestrator: DocumentProcessingOrchestrator):
    """Verify processing aborts gracefully on unsupported MIME types."""
    file_path = tmp_path / "image.png"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    context = DocumentProcessingContext(
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        file_path=file_path,
        original_filename="image.png",
        mime_type="image/png",
    )

    with pytest.raises(ParseUnsupportedTypeError):
        orchestrator.process_document(context)


def test_empty_document(tmp_path: Path, orchestrator: DocumentProcessingOrchestrator):
    """Verify processing aborts cleanly on an empty document."""
    file_path = tmp_path / "empty.md"
    file_path.write_text("   \n   \n", encoding="utf-8")

    context = DocumentProcessingContext(
        document_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        file_path=file_path,
        original_filename="empty.md",
        mime_type="text/markdown",
    )

    with pytest.raises(ParseEmptyDocumentError):
        orchestrator.process_document(context)
