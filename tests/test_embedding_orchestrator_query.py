"""Unit tests for EmbeddingOrchestrator query embedding functionality."""

import pytest
from unittest.mock import Mock

from app.common.exceptions import SentinelProviderError, SentinelValidationError
from app.llms.embeddings.base import BaseEmbeddingProvider
from app.llms.embeddings.models import EmbeddingRequest, EmbeddingResponse
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator


class TestEmbeddingOrchestratorQueryEmbedding:
    """Test the embed_query method added in Phase 10.4."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock embedding provider."""
        return Mock(spec=BaseEmbeddingProvider)

    @pytest.fixture
    def orchestrator(self, mock_provider):
        """Create an orchestrator with mocked provider."""
        return EmbeddingOrchestrator(provider=mock_provider, batch_size=32)

    def test_embed_query_generates_single_vector(self, orchestrator, mock_provider):
        """Test that embed_query generates a single embedding vector."""
        # Setup mock response
        test_vector = [0.1] * 384
        mock_provider.embed.return_value = EmbeddingResponse(
            embeddings=[test_vector],
            dimensions=384,
            provider="test-provider",
            model="test-model",
            processing_time_ms=10.0,
        )

        # Execute
        result = orchestrator.embed_query("What is the deployment process?")

        # Verify
        assert result == test_vector
        assert len(result) == 384
        mock_provider.embed.assert_called_once()
        call_args = mock_provider.embed.call_args[0][0]
        assert isinstance(call_args, EmbeddingRequest)
        assert call_args.texts == ["What is the deployment process?"]

    def test_embed_query_rejects_empty_string(self, orchestrator, mock_provider):
        """Test that embed_query rejects empty queries."""
        with pytest.raises(SentinelValidationError) as exc_info:
            orchestrator.embed_query("")

        assert "empty query" in str(exc_info.value).lower()
        mock_provider.embed.assert_not_called()

    def test_embed_query_rejects_whitespace_only(self, orchestrator, mock_provider):
        """Test that embed_query rejects whitespace-only queries."""
        with pytest.raises(SentinelValidationError) as exc_info:
            orchestrator.embed_query("   \n\t  ")

        assert "empty query" in str(exc_info.value).lower()
        mock_provider.embed.assert_not_called()

    def test_embed_query_validates_response_count(self, orchestrator, mock_provider):
        """Test that embed_query validates provider returns exactly 1 embedding."""
        # Provider returns wrong number of embeddings
        mock_provider.embed.return_value = EmbeddingResponse(
            embeddings=[[0.1] * 384, [0.2] * 384],  # Two instead of one
            dimensions=384,
            provider="test-provider",
            model="test-model",
            processing_time_ms=10.0,
        )

        with pytest.raises(SentinelProviderError) as exc_info:
            orchestrator.embed_query("test query")

        assert "2 embeddings" in str(exc_info.value)
        assert "expected 1" in str(exc_info.value)

    def test_embed_query_validates_non_empty_vector(self, orchestrator, mock_provider):
        """Test that embed_query validates provider returns non-empty vector."""
        # Provider returns empty vector
        mock_provider.embed.return_value = EmbeddingResponse(
            embeddings=[[]],
            dimensions=384,
            provider="test-provider",
            model="test-model",
            processing_time_ms=10.0,
        )

        with pytest.raises(SentinelProviderError) as exc_info:
            orchestrator.embed_query("test query")

        assert "empty embedding vector" in str(exc_info.value).lower()

    def test_embed_query_validates_dimension_consistency(self, orchestrator, mock_provider):
        """Test that embed_query validates dimension metadata matches vector length."""
        # Dimension mismatch
        test_vector = [0.1] * 384
        mock_provider.embed.return_value = EmbeddingResponse(
            embeddings=[test_vector],
            dimensions=512,  # Wrong dimension
            provider="test-provider",
            model="test-model",
            processing_time_ms=10.0,
        )

        with pytest.raises(SentinelProviderError) as exc_info:
            orchestrator.embed_query("test query")

        assert "dimension" in str(exc_info.value).lower()
        assert "512" in str(exc_info.value)
        assert "384" in str(exc_info.value)
