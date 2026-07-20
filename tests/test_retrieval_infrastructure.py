"""Infrastructure and integration tests for the retrieval module.

These tests validate the retrieval module's contracts, exceptions,
dependency injection, and integration with real Qdrant infrastructure.
"""

import pytest
from qdrant_client.models import Distance, Filter, FieldCondition, MatchValue

from app.common.exceptions import SentinelBaseException
from app.config.settings import Settings
from app.modules.retrieval.dependencies import get_retrieval_service
from app.modules.retrieval.exceptions import SentinelRetrievalError
from app.modules.retrieval.service import RetrievalService
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.config import CollectionConfig
from app.vectorstore.collections.manager import CollectionManager
from app.vectorstore.repositories.models import VectorPoint, VectorSearchParams, UpsertBatchRequest
from app.vectorstore.repositories.repository import VectorRepository

# Deterministic test vectors (384 dimensions for BGE-M3 compatibility)
DIMENSIONS = 384
QUERY_VECTOR = [0.1] * DIMENSIONS
SIMILAR_VECTOR_1 = [0.11] * DIMENSIONS  # Cosine similarity ≈ 0.99+
SIMILAR_VECTOR_2 = [0.12] * DIMENSIONS  # Cosine similarity ≈ 0.98+
DISSIMILAR_VECTOR = [-0.9] * DIMENSIONS  # Cosine similarity < 0


class TestVectorSearchParamsModel:
    """Test the VectorSearchParams model used by retrieval."""

    def test_instantiation_with_required_fields(self):
        """Test creating VectorSearchParams with required fields only."""
        params = VectorSearchParams(
            collection_name="test_collection",
            vector=[0.1, 0.2, 0.3],
            limit=10,
        )
        assert params.collection_name == "test_collection"
        assert params.vector == [0.1, 0.2, 0.3]
        assert params.limit == 10
        assert params.score_threshold is None
        assert params.filter is None

    def test_instantiation_with_optional_fields(self):
        """Test creating VectorSearchParams with all fields."""
        qdrant_filter = Filter(
            must=[FieldCondition(key="workspace_id", match=MatchValue(value="test-workspace"))]
        )
        params = VectorSearchParams(
            collection_name="test_collection",
            vector=[0.1, 0.2, 0.3],
            limit=5,
            score_threshold=0.7,
            filter=qdrant_filter,
        )
        assert params.collection_name == "test_collection"
        assert params.vector == [0.1, 0.2, 0.3]
        assert params.limit == 5
        assert params.score_threshold == 0.7
        assert params.filter == qdrant_filter

    def test_accepts_qdrant_filter_type(self):
        """Test that VectorSearchParams accepts Qdrant Filter objects."""
        qdrant_filter = Filter(
            must=[
                FieldCondition(key="document_id", match=MatchValue(value="doc-123")),
                FieldCondition(key="page_number", match=MatchValue(value=5)),
            ]
        )
        params = VectorSearchParams(
            collection_name="documents",
            vector=[0.5] * 384,
            limit=10,
            filter=qdrant_filter,
        )
        assert params.filter is not None
        assert len(params.filter.must) == 2


class TestSentinelRetrievalError:
    """Test the SentinelRetrievalError exception."""

    def test_instantiation(self):
        """Test creating a SentinelRetrievalError."""
        error = SentinelRetrievalError("Retrieval operation failed")
        assert error.message == "Retrieval operation failed"
        assert error.code == "RETRIEVAL_ERROR"
        assert error.http_status == 500

    def test_inheritance(self):
        """Test that SentinelRetrievalError inherits from SentinelBaseException."""
        error = SentinelRetrievalError("Test error")
        assert isinstance(error, SentinelBaseException)
        assert isinstance(error, Exception)

    def test_error_properties(self):
        """Test that error properties are correctly set."""
        error = SentinelRetrievalError("Vector store connection failed")
        assert str(error) == "Vector store connection failed"
        assert error.code == "RETRIEVAL_ERROR"
        assert error.http_status == 500


# ── Integration Tests with Real Qdrant ────────────────────────────────────────


@pytest.fixture
async def qdrant_manager():
    """Provide a QdrantConnectionManager for integration tests."""
    settings = Settings()
    manager = QdrantConnectionManager(settings=settings)
    await manager.check_health()
    yield manager
    await manager.close()


@pytest.fixture
async def test_collection(qdrant_manager):
    """Create a temporary test collection for retrieval tests."""
    collection_name = "test_retrieval_collection"
    collection_manager = CollectionManager(qdrant_manager=qdrant_manager)
    
    config = CollectionConfig(
        name=collection_name,
        vector_size=DIMENSIONS,
        distance=Distance.COSINE,
    )
    
    await collection_manager.ensure_collection(config)
    yield collection_name
    await collection_manager.delete_collection(collection_name)


@pytest.fixture
async def vector_repo(qdrant_manager):
    """Provide a VectorRepository for integration tests."""
    return VectorRepository(qdrant_manager=qdrant_manager)


@pytest.fixture
async def retrieval_service(vector_repo):
    """Provide a RetrievalService for integration tests."""
    return RetrievalService(vector_repository=vector_repo)


@pytest.fixture
async def populated_collection(test_collection, vector_repo):
    """Populate test collection with deterministic vectors and metadata."""
    points = [
        VectorPoint(
            id="00000000-0000-0000-0000-000000000001",
            vector=SIMILAR_VECTOR_1,
            payload={"type": "similar", "workspace_id": "workspace-1", "document_id": "doc-1"},
        ),
        VectorPoint(
            id="00000000-0000-0000-0000-000000000002",
            vector=SIMILAR_VECTOR_2,
            payload={"type": "similar", "workspace_id": "workspace-1", "document_id": "doc-2"},
        ),
        VectorPoint(
            id="00000000-0000-0000-0000-000000000003",
            vector=DISSIMILAR_VECTOR,
            payload={"type": "dissimilar", "workspace_id": "workspace-2", "document_id": "doc-3"},
        ),
    ]
    
    request = UpsertBatchRequest(
        collection_name=test_collection,
        points=points,
    )
    await vector_repo.upsert_batch(request)
    
    yield test_collection


class TestRetrievalIntegration:
    """Integration tests with real Qdrant infrastructure."""

    async def test_retrieve_returns_results(self, retrieval_service, populated_collection):
        """Test successful retrieval returns VectorSearchResult list."""
        params = VectorSearchParams(
            collection_name=populated_collection,
            vector=QUERY_VECTOR,
            limit=10,
        )
        results = await retrieval_service.retrieve(params)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(hasattr(r, "score") for r in results)
        assert all(hasattr(r, "payload") for r in results)

    async def test_retrieve_orders_by_similarity(self, retrieval_service, populated_collection):
        """Test results are ordered by descending similarity score."""
        params = VectorSearchParams(
            collection_name=populated_collection,
            vector=QUERY_VECTOR,
            limit=10,
        )
        results = await retrieval_service.retrieve(params)
        
        assert len(results) >= 2
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True), "Results should be ordered by score descending"
        
        # Verify similar vectors score higher than dissimilar
        similar_ids = {"00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"}
        top_result_id = results[0].id
        assert top_result_id in similar_ids, "Most similar vector should rank first"

    async def test_retrieve_respects_limit(self, retrieval_service, populated_collection):
        """Test limit parameter controls result count."""
        params = VectorSearchParams(
            collection_name=populated_collection,
            vector=QUERY_VECTOR,
            limit=2,
        )
        results = await retrieval_service.retrieve(params)
        
        assert len(results) == 2, "Should return exactly 2 results when limit=2"

    async def test_retrieve_applies_score_threshold(self, retrieval_service, populated_collection):
        """Test score_threshold filters low-scoring results."""
        params = VectorSearchParams(
            collection_name=populated_collection,
            vector=QUERY_VECTOR,
            limit=10,
            score_threshold=0.5,
        )
        results = await retrieval_service.retrieve(params)
        
        assert all(r.score >= 0.5 for r in results), "All results should meet score threshold"
        
        # Dissimilar vector should be filtered out (negative similarity with threshold)
        result_ids = {r.id for r in results}
        assert "00000000-0000-0000-0000-000000000003" not in result_ids, "Dissimilar vector should be filtered by threshold"

    async def test_retrieve_applies_metadata_filter(self, retrieval_service, populated_collection):
        """Test Qdrant Filter correctly filters by metadata."""
        qdrant_filter = Filter(
            must=[FieldCondition(key="workspace_id", match=MatchValue(value="workspace-1"))]
        )
        params = VectorSearchParams(
            collection_name=populated_collection,
            vector=QUERY_VECTOR,
            limit=10,
            filter=qdrant_filter,
        )
        results = await retrieval_service.retrieve(params)
        
        assert len(results) == 2, "Should only return vectors from workspace-1"
        for result in results:
            assert result.payload is not None
            assert result.payload["workspace_id"] == "workspace-1"

    async def test_retrieve_returns_empty_for_no_matches(self, retrieval_service, test_collection):
        """Test retrieval returns empty list when no vectors exist."""
        params = VectorSearchParams(
            collection_name=test_collection,
            vector=QUERY_VECTOR,
            limit=10,
        )
        results = await retrieval_service.retrieve(params)
        
        assert results == [], "Should return empty list for empty collection"

    async def test_retrieve_raises_error_for_nonexistent_collection(self, retrieval_service):
        """Test retrieval fails gracefully for missing collection."""
        params = VectorSearchParams(
            collection_name="nonexistent_collection_12345",
            vector=QUERY_VECTOR,
            limit=10,
        )
        
        with pytest.raises(SentinelRetrievalError) as exc_info:
            await retrieval_service.retrieve(params)
        
        error = exc_info.value
        assert "nonexistent_collection_12345" in error.message
        assert error.code == "RETRIEVAL_ERROR"
        assert error.http_status == 500

    async def test_retrieve_preserves_exception_chaining(self, retrieval_service):
        """Test that VectorStoreError is chained when wrapped in RetrievalError."""
        params = VectorSearchParams(
            collection_name="nonexistent_collection_67890",
            vector=QUERY_VECTOR,
            limit=10,
        )
        
        with pytest.raises(SentinelRetrievalError) as exc_info:
            await retrieval_service.retrieve(params)
        
        error = exc_info.value
        assert error.__cause__ is not None, "Original exception should be chained"
