"""Shared testing utilities and fixtures for Sentinel AI."""

import uuid
from typing import Iterator

import pytest

from app.config.settings import Settings
from app.llms.embeddings.base import BaseEmbeddingProvider
from app.llms.embeddings.factory import get_embedding_provider
from app.llms.embeddings.models import EmbeddingRequest, EmbeddingResponse
from app.modules.ingestion.metadata.models import ProcessedChunk


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    A deterministic mock provider for testing embedding orchestration and failure modes.
    
    Attributes:
        call_count: Tracks how many times `embed()` is invoked.
        fail_mode: Configures the mock to intentionally fail in specific ways.
            Supported modes:
            - 'count_mismatch': Returns fewer vectors than requested texts.
            - 'dimension_mismatch': Returns vectors of varying lengths.
            - 'empty_vector': Returns an empty array `[]` for one of the vectors.
    """
    def __init__(self):
        self.call_count = 0
        self.fail_mode: str | None = None
        self.dimension = 384

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.call_count += 1
        
        if self.fail_mode == "count_mismatch":
            embeddings = [[0.1] * self.dimension for _ in range(max(0, len(request.texts) - 1))]
        elif self.fail_mode == "dimension_mismatch":
            embeddings = [[0.1] * self.dimension for _ in request.texts]
            if len(embeddings) > 1:
                embeddings[1] = [0.1] * (self.dimension + 1)
        elif self.fail_mode == "empty_vector":
            embeddings = [[0.1] * self.dimension for _ in request.texts]
            if embeddings:
                embeddings[0] = []
        else:
            embeddings = [[0.1] * self.dimension for _ in request.texts]
            
        return EmbeddingResponse(
            embeddings=embeddings,
            dimensions=self.dimension,
            provider="mock_provider",
            model="mock_model",
            processing_time_ms=10.0
        )


@pytest.fixture
def mock_provider() -> MockEmbeddingProvider:
    """Provides a fresh MockEmbeddingProvider for deterministic testing."""
    return MockEmbeddingProvider()


@pytest.fixture
def real_provider() -> BaseEmbeddingProvider:
    """Provides the real BgeM3EmbeddingProvider (used ONLY for smoke tests)."""
    settings = Settings()
    settings.embedding_provider = "bge_m3"
    return get_embedding_provider(settings)


@pytest.fixture
def dummy_chunks():
    """Factory fixture to generate N deterministic ProcessedChunk instances."""
    def _create(count: int) -> list[ProcessedChunk]:
        return [
            ProcessedChunk(
                chunk_id=f"chunk-{i}",
                document_id=uuid.UUID(int=i),
                workspace_id=uuid.UUID(int=100),
                chunk_index=i,
                content=f"Deterministic content {i}",
                character_count=25,
                token_count=5,
                page_number=1,
            )
            for i in range(count)
        ]
    return _create
