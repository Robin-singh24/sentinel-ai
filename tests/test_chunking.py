"""Unit tests for the chunking engine."""

import pytest

from app.common.exceptions import SentinelValidationError
from app.modules.ingestion.chunking import TextChunker
from app.modules.ingestion.normalization.models import NormalizedDocument
from app.modules.ingestion.parsers.base import DocumentType


def _make_doc(text: str) -> NormalizedDocument:
    return NormalizedDocument(
        normalized_text=text,
        original_filename="test.txt",
        document_type=DocumentType.text,
        page_count=1,
    )


def test_invalid_configuration():
    """Verify that chunk size and overlap are validated."""
    with pytest.raises(SentinelValidationError, match="greater than 0"):
        TextChunker(chunk_size=0, chunk_overlap=0)

    with pytest.raises(SentinelValidationError, match="less than chunk_size"):
        TextChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(SentinelValidationError, match="non-negative"):
        TextChunker(chunk_size=100, chunk_overlap=-1)


def test_empty_document():
    """Verify empty documents yield an empty list."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk(_make_doc("   "))
    assert len(chunks) == 0


def test_document_smaller_than_chunk_size():
    """Verify a small document yields exactly one chunk."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = "Hello, Sentinel AI."
    chunks = chunker.chunk(_make_doc(text))

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == text
    assert chunks[0].character_count == len(text)


def test_multi_chunk_ordering_and_overlap():
    """Verify chunk generation and overlap correctly span multiple chunks."""
    text = "A " * 50  # 100 characters total
    chunker = TextChunker(chunk_size=40, chunk_overlap=10)
    chunks = chunker.chunk(_make_doc(text))

    assert len(chunks) > 1
    for i, c in enumerate(chunks):
        assert c.chunk_index == i
        assert c.character_count <= 40
        assert c.content.strip() != ""

    # Check overlap explicitly: Chunk 0 ends with some text that should appear at start of Chunk 1
    # Since trailing spaces are stripped, we take a substring without trailing space.
    overlap_text = chunks[1].content[:5]
    assert chunks[0].content.endswith(overlap_text)


def test_paragraph_boundary_preservation():
    """Verify that the chunker splits on double newlines where possible."""
    # "para 1\n\npara 2\n\npara 3"
    text = "para 1\n\npara 2\n\npara 3"
    chunker = TextChunker(chunk_size=20, chunk_overlap=5)
    chunks = chunker.chunk(_make_doc(text))

    # length of "para 1\n\npara 2" is 14. length of "para 1\n\npara 2\n\n" is 16.
    # The chunker finds the \n\n at index 14 and cuts at 16.
    assert chunks[0].content == "para 1\n\npara 2"
    # Overlap targets 16 - 5 = 11. Text[11:16] is "a 2\n\n". 
    # It finds \n\n, and starts the next chunk at 16.
    assert chunks[1].content == "para 3"


def test_word_boundary_preservation():
    """Verify the chunker splits on spaces, not middle of words."""
    # "abcdefghijk lmnopqrst" -> length is 21. space is at index 11.
    text = "abcdefghijk lmnopqrst"
    chunker = TextChunker(chunk_size=15, chunk_overlap=0)
    chunks = chunker.chunk(_make_doc(text))

    assert len(chunks) == 2
    assert chunks[0].content == "abcdefghijk"
    assert chunks[1].content == "lmnopqrst"


def test_hard_cut_when_no_boundary_exists():
    """Verify fallback to hard character cut if no semantic boundary exists."""
    text = "a" * 100
    chunker = TextChunker(chunk_size=40, chunk_overlap=5)
    chunks = chunker.chunk(_make_doc(text))

    assert len(chunks) == 3
    assert chunks[0].content == "a" * 40
    # Next start is 40 - 5 = 35. Text[35:75] is 40 chars.
    assert chunks[1].content == "a" * 40
    # Next start is 75 - 5 = 70. Text[70:100] is 30 chars.
    assert chunks[2].content == "a" * 30


def test_deterministic_output():
    """Verify that multiple runs with the same input produce identical chunks."""
    text = "Sentence one. \n\n Sentence two. \n\n Sentence three."
    chunker = TextChunker(chunk_size=25, chunk_overlap=5)

    run_1 = chunker.chunk(_make_doc(text))
    run_2 = chunker.chunk(_make_doc(text))
    run_3 = chunker.chunk(_make_doc(text))

    assert run_1 == run_2 == run_3
