"""Unit tests for the retrieval module isolating the RetrievalService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.retrieval.dependencies import get_retrieval_service
from app.modules.retrieval.exceptions import SentinelRetrievalError
from app.modules.retrieval.service import RetrievalService
from app.vectorstore.exceptions import SentinelVectorStoreError
from app.vectorstore.repositories.models import VectorSearchParams, VectorSearchResult
from app.vectorstore.repositories.repository import VectorRepository


@pytest.fixture
def mock_vector_repo():
    """Provide a mocked VectorRepository."""
    repo = MagicMock(spec=VectorRepository)
    repo.search = AsyncMock()
    return repo


@pytest.fixture
def retrieval_service(mock_vector_repo):
    """Provide a RetrievalService injected with a mocked VectorRepository."""
    return RetrievalService(vector_repository=mock_vector_repo)


class TestRetrievalServiceUnit:
    """Unit tests for RetrievalService business logic (error wrapping)."""

    async def test_retrieve_success(self, retrieval_service, mock_vector_repo):
        """Test retrieve successfully delegates and returns results."""
        params = VectorSearchParams(
            collection_name="test_collection",
            vector=[0.1, 0.2, 0.3],
            limit=5,
        )
        
        mock_results = [
            VectorSearchResult(id="doc-1", score=0.9, payload={"text": "hello"}),
            VectorSearchResult(id="doc-2", score=0.8, payload={"text": "world"}),
        ]
        mock_vector_repo.search.return_value = mock_results
        
        results = await retrieval_service.retrieve(params)
        
        mock_vector_repo.search.assert_awaited_once_with(params)
        assert results == mock_results
        assert len(results) == 2

    async def test_retrieve_wraps_vector_store_error(self, retrieval_service, mock_vector_repo):
        """Test retrieve catches SentinelVectorStoreError and raises SentinelRetrievalError."""
        params = VectorSearchParams(
            collection_name="test_collection",
            vector=[0.1, 0.2, 0.3],
            limit=5,
        )
        
        original_error = SentinelVectorStoreError("Connection timeout")
        mock_vector_repo.search.side_effect = original_error
        
        with pytest.raises(SentinelRetrievalError) as exc_info:
            await retrieval_service.retrieve(params)
            
        error = exc_info.value
        assert "Failed to retrieve from collection 'test_collection'" in error.message
        assert "Connection timeout" in error.message
        assert error.code == "RETRIEVAL_ERROR"
        assert error.http_status == 500

    async def test_retrieve_preserves_exception_chaining(self, retrieval_service, mock_vector_repo):
        """Test the original exception is preserved in __cause__."""
        params = VectorSearchParams(
            collection_name="test_collection",
            vector=[0.1, 0.2, 0.3],
            limit=5,
        )
        
        original_error = SentinelVectorStoreError("Index not ready")
        mock_vector_repo.search.side_effect = original_error
        
        with pytest.raises(SentinelRetrievalError) as exc_info:
            await retrieval_service.retrieve(params)
            
        error = exc_info.value
        assert error.__cause__ is original_error

    async def test_retrieve_allows_other_exceptions_to_propagate(self, retrieval_service, mock_vector_repo):
        """Test retrieve does not wrap standard Python exceptions."""
        params = VectorSearchParams(
            collection_name="test_collection",
            vector=[0.1, 0.2, 0.3],
            limit=5,
        )
        
        mock_vector_repo.search.side_effect = ValueError("Invalid input")
        
        with pytest.raises(ValueError) as exc_info:
            await retrieval_service.retrieve(params)
            
        assert str(exc_info.value) == "Invalid input"


class TestRetrievalDependencyInjection:
    """Unit tests for dependency injection composition."""

    def test_get_retrieval_service(self, mock_vector_repo):
        """Test get_retrieval_service composes dependencies correctly."""
        service = get_retrieval_service(vector_repo=mock_vector_repo)
        assert isinstance(service, RetrievalService)
        assert service._vector_repo is mock_vector_repo
