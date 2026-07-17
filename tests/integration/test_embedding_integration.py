"""Integration and regression tests for the Embedding Orchestrator."""

import math
import pytest

from app.common.exceptions import SentinelProviderError, SentinelValidationError
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator
from tests.conftest import MockEmbeddingProvider


def test_smoke_real_provider(real_provider, dummy_chunks):
    """
    Smoke Test: Verify model loads, provider works, and valid embedding is produced.
    This is the ONLY test that uses the real 2GB Hugging Face model to avoid slow tests.
    """
    orchestrator = EmbeddingOrchestrator(real_provider, batch_size=1)
    chunks = dummy_chunks(1)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == 1
    assert result[0].dimensions > 0
    assert len(result[0].vector) == result[0].dimensions


def test_single_chunk(mock_provider, dummy_chunks):
    """Verify single chunk embedding: metadata preserved, non-empty, dimensions > 0."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    chunks = dummy_chunks(1)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == 1
    embedded = result[0]
    assert embedded.chunk == chunks[0]  # Metadata perfectly preserved (immutable ref)
    assert embedded.dimensions > 0
    assert len(embedded.vector) == embedded.dimensions
    assert mock_provider.call_count == 1


def test_multiple_chunks(mock_provider, dummy_chunks):
    """Verify multiple chunks: counts match, ordering preserved, dimensions identical."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    chunks = dummy_chunks(5)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == 5
    for i, embedded in enumerate(result):
        assert embedded.chunk.chunk_index == i  # Ordering preserved
        assert embedded.dimensions == mock_provider.dimension
        assert len(embedded.vector) > 0


def test_batch_size_one(mock_provider, dummy_chunks):
    """Verify batch_size=1 processes every chunk preserving order."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=1)
    chunks = dummy_chunks(5)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == 5
    assert mock_provider.call_count == 5  # Called exactly 5 times
    for i, embedded in enumerate(result):
        assert embedded.chunk.chunk_id == chunks[i].chunk_id


def test_batch_size_default(mock_provider, dummy_chunks):
    """Verify default batch size works (usually 32)."""
    from app.config.settings import Settings
    settings = Settings()
    default_batch = settings.embedding_batch_size
    
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=default_batch)
    chunks = dummy_chunks(default_batch * 2)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == len(chunks)
    assert mock_provider.call_count == 2


def test_batch_size_larger_than_input(mock_provider, dummy_chunks):
    """Verify processing when input is smaller than batch size."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=64)
    chunks = dummy_chunks(10)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == 10
    assert mock_provider.call_count == 1


def test_uneven_final_batch(mock_provider, dummy_chunks):
    """Verify 75 chunks with batch_size 32 works successfully (32, 32, 11)."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    chunks = dummy_chunks(75)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == 75
    assert mock_provider.call_count == 3
    # First item of the last batch should be index 64
    assert result[64].chunk.chunk_index == 64


def test_metadata_preservation(mock_provider, dummy_chunks):
    """Verify exact fields remain completely unchanged via immutability."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    original = dummy_chunks(1)[0]
    
    result = orchestrator.embed([original])
    embedded_chunk = result[0].chunk
    
    assert embedded_chunk.chunk_id == original.chunk_id
    assert embedded_chunk.document_id == original.document_id
    assert embedded_chunk.workspace_id == original.workspace_id
    assert embedded_chunk.chunk_index == original.chunk_index
    assert embedded_chunk.page_number == original.page_number
    assert embedded_chunk.character_count == original.character_count
    assert embedded_chunk.token_count == original.token_count


def test_empty_input(mock_provider):
    """Verify empty input fails fast."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    with pytest.raises(SentinelValidationError, match="empty list"):
        orchestrator.embed([])


def test_invalid_batch_size(mock_provider):
    """Verify invalid batch sizes fail fast on initialization."""
    with pytest.raises(SentinelValidationError, match="batch size"):
        EmbeddingOrchestrator(mock_provider, batch_size=0)
        
    with pytest.raises(SentinelValidationError):
        EmbeddingOrchestrator(mock_provider, batch_size=-5)


def test_provider_count_mismatch(mock_provider, dummy_chunks):
    """Verify exception when provider returns wrong number of vectors."""
    mock_provider.fail_mode = "count_mismatch"
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    
    with pytest.raises(SentinelProviderError, match="expected 2"):
        orchestrator.embed(dummy_chunks(2))


def test_provider_dimension_mismatch(mock_provider, dummy_chunks):
    """Verify exception when a vector dimension shifts mid-batch."""
    mock_provider.fail_mode = "dimension_mismatch"
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    
    with pytest.raises(SentinelProviderError, match="Dimension mismatch"):
        orchestrator.embed(dummy_chunks(2))


def test_provider_empty_vector(mock_provider, dummy_chunks):
    """Verify exception when provider returns an empty list for a vector."""
    mock_provider.fail_mode = "empty_vector"
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    
    with pytest.raises(SentinelProviderError, match="empty"):
        orchestrator.embed(dummy_chunks(1))


def test_deterministic_structure(mock_provider, dummy_chunks):
    """Verify identical inputs yield identically structured outputs."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=32)
    
    chunks_1 = dummy_chunks(10)
    result_1 = orchestrator.embed(chunks_1)
    
    chunks_2 = dummy_chunks(10)
    result_2 = orchestrator.embed(chunks_2)
    
    for r1, r2 in zip(result_1, result_2):
        assert r1.chunk.chunk_id == r2.chunk.chunk_id
        assert r1.dimensions == r2.dimensions
        # Vectors are dummy data here, so they will be identical too,
        # but the core requirement is identical chunks/metadata.


@pytest.mark.parametrize("input_size", [32, 33, 64, 65])
def test_batch_boundary_regression(mock_provider, dummy_chunks, input_size):
    """
    Verify batching behaves precisely on mathematically critical boundaries.
    Validates ordering, count, metadata, and exact call counts.
    """
    batch_size = 32
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=batch_size)
    chunks = dummy_chunks(input_size)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == input_size
    assert mock_provider.call_count == math.ceil(input_size / batch_size)
    
    for i, embedded in enumerate(result):
        assert embedded.chunk.chunk_index == i
        assert embedded.dimensions == mock_provider.dimension


@pytest.mark.parametrize("test_batch_size", [1, 32, 64])
def test_regression_across_batch_sizes(mock_provider, dummy_chunks, test_batch_size):
    """Verify output logic is completely identical regardless of the configured batch size."""
    orchestrator = EmbeddingOrchestrator(mock_provider, batch_size=test_batch_size)
    chunks = dummy_chunks(100)
    
    result = orchestrator.embed(chunks)
    
    assert len(result) == 100
    assert result[0].chunk.chunk_index == 0
    assert result[-1].chunk.chunk_index == 99
    assert mock_provider.call_count == math.ceil(100 / test_batch_size)
