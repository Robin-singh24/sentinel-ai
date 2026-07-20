"""Integration tests for the Supervisor orchestrator.

These tests validate the full execution chain from Intent Classification
to Qdrant vector retrieval using real dependencies.
"""

import pytest
from qdrant_client.models import Distance

from app.agents.supervisor.classifier import IntentClassifier
from app.agents.supervisor.models import WorkflowExecutionResult
from app.agents.supervisor.planner import WorkflowPlanner
from app.agents.supervisor.service import SupervisorService
from app.config.settings import Settings
from app.llms.embeddings.factory import get_embedding_provider
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator
from app.modules.retrieval.service import RetrievalService
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.config import CollectionConfig
from app.vectorstore.collections.manager import CollectionManager
from app.vectorstore.repositories.models import VectorPoint, UpsertBatchRequest
from app.vectorstore.repositories.repository import VectorRepository

# Deterministic test vectors (384 dimensions for BGE-M3 compatibility)
DIMENSIONS = 384
QUERY_VECTOR = [0.1] * DIMENSIONS
SIMILAR_VECTOR_1 = [0.11] * DIMENSIONS
SIMILAR_VECTOR_2 = [0.12] * DIMENSIONS


@pytest.fixture
def settings():
    """Provide configuration settings."""
    # Ensure local qdrant host and valid embedding provider
    return Settings(
        qdrant_host="localhost",
        embedding_provider="bge_m3"
    )


@pytest.fixture
async def qdrant_manager(settings):
    """Provide a QdrantConnectionManager for integration tests."""
    manager = QdrantConnectionManager(settings=settings)
    await manager.check_health()
    yield manager
    await manager.close()


@pytest.fixture
async def test_collection(qdrant_manager):
    """Create a temporary test collection for supervisor integration tests."""
    # We use "documents" because SupervisorService hardcodes the target collection
    # We must ensure this runs isolated or cleans up properly.
    # To be safe, we'll create the collection expected by the Supervisor.
    collection_name = "documents"
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
async def populated_collection(test_collection, vector_repo):
    """Populate test collection with deterministic vectors and metadata."""
    points = [
        VectorPoint(
            id="00000000-0000-0000-0000-000000000001",
            vector=SIMILAR_VECTOR_1,
            payload={"text": "Integration test doc 1", "workspace_id": "ws-1"},
        ),
        VectorPoint(
            id="00000000-0000-0000-0000-000000000002",
            vector=SIMILAR_VECTOR_2,
            payload={"text": "Integration test doc 2", "workspace_id": "ws-1"},
        ),
    ]
    
    request = UpsertBatchRequest(
        collection_name=test_collection,
        points=points,
    )
    await vector_repo.upsert_batch(request)
    
    yield test_collection


@pytest.fixture
def real_embedding_orchestrator(settings):
    """Provide a real EmbeddingOrchestrator."""
    # This assumes the provider can be instantiated and run locally or mockingly
    # depending on EMBEDDING_PROVIDER in settings.
    provider = get_embedding_provider(settings)
    
    # We patch embed_query to just return our deterministic QUERY_VECTOR 
    # to avoid needing a real LLM for the integration test, 
    # but still execute the orchestrator layer.
    orchestrator = EmbeddingOrchestrator(
        provider=provider,
        batch_size=settings.embedding_batch_size,
    )
    
    # Simple monkeypatch for deterministic test vector
    def mock_embed_query(text: str) -> list[float]:
        return QUERY_VECTOR
        
    orchestrator.embed_query = mock_embed_query
    return orchestrator


@pytest.fixture
def supervisor_service(
    vector_repo,
    real_embedding_orchestrator,
    settings,
):
    """Provide a SupervisorService with real (or semi-real) dependencies."""
    intent_classifier = IntentClassifier()
    workflow_planner = WorkflowPlanner()
    retrieval_service = RetrievalService(vector_repository=vector_repo)
    
    return SupervisorService(
        intent_classifier=intent_classifier,
        workflow_planner=workflow_planner,
        embedding_orchestrator=real_embedding_orchestrator,
        retrieval_service=retrieval_service,
        settings=settings,
    )


class TestSupervisorIntegration:
    """End-to-End integration tests for Supervisor Orchestration."""

    async def test_process_query_end_to_end(self, supervisor_service, populated_collection):
        """Test the complete workflow from query to Qdrant retrieval.
        
        Validates that the WorkflowExecutionResult is the only public output contract
        and no internal implementation details leak through.
        """
        query = "How do I test integration?"
        
        # Execute the full real chain
        result = await supervisor_service.process_query(query, limit=5)
        
        # 1. Verify contract type
        assert type(result) is WorkflowExecutionResult, (
            "Result must be exactly WorkflowExecutionResult, no subclass or internal type."
        )
        
        # 2. Verify results are populated
        assert len(result.retrieved_chunks) > 0, "Expected to retrieve vectors from Qdrant"
        
        # 3. Verify internal details do not leak (e.g. no Qdrant specifics exposed)
        # VectorSearchResult is part of our domain, but we ensure it doesn't expose qdrant raw objects
        for chunk in result.retrieved_chunks:
            assert hasattr(chunk, "id")
            assert hasattr(chunk, "score")
            assert hasattr(chunk, "payload")
            # The payload should just be a dict, not a Qdrant Payload object
            assert isinstance(chunk.payload, dict)
            # Ensure it actually came from our populated collection
            assert chunk.payload.get("workspace_id") == "ws-1"
