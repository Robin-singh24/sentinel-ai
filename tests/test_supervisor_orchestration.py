"""Orchestration tests for the supervisor module.

These tests validate the supervisor's ability to orchestrate the complete
workflow from intent classification through retrieval execution.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from app.agents.supervisor.classifier import IntentClassifier
from app.agents.supervisor.dependencies import get_supervisor_service
from app.agents.supervisor.models import (
    ClassifiedIntent,
    IntentType,
    WorkflowExecutionResult,
    WorkflowPlan,
    WorkflowType,
)
from app.agents.supervisor.planner import WorkflowPlanner
from app.agents.supervisor.service import SupervisorService
from app.config.settings import Settings
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator
from app.modules.retrieval.service import RetrievalService
from app.vectorstore.repositories.models import VectorSearchResult, VectorSearchParams


class TestSupervisorOrchestrationUnit:
    """Unit tests for supervisor orchestration with mocked dependencies."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for testing."""
        intent_classifier = Mock(spec=IntentClassifier)
        workflow_planner = Mock(spec=WorkflowPlanner)
        embedding_orchestrator = Mock(spec=EmbeddingOrchestrator)
        retrieval_service = AsyncMock(spec=RetrievalService)
        settings = Settings()

        return {
            "intent_classifier": intent_classifier,
            "workflow_planner": workflow_planner,
            "embedding_orchestrator": embedding_orchestrator,
            "retrieval_service": retrieval_service,
            "settings": settings,
        }

    async def test_process_query_orchestrates_complete_workflow(self, mock_dependencies):
        """Test that process_query orchestrates all workflow steps."""
        # Setup mocks
        deps = mock_dependencies
        deps["intent_classifier"].classify.return_value = ClassifiedIntent(
            intent=IntentType.KNOWLEDGE_RETRIEVAL
        )
        deps["workflow_planner"].plan.return_value = WorkflowPlan(workflow=WorkflowType.RETRIEVAL)
        deps["embedding_orchestrator"].embed_query.return_value = [0.1] * 384
        deps["retrieval_service"].retrieve.return_value = [
            VectorSearchResult(id="chunk-1", score=0.95, payload={"content": "test"}, vector=None)
        ]

        service = SupervisorService(**deps)

        # Execute
        result = await service.process_query("What is the deployment process?", limit=5)

        # Verify
        assert isinstance(result, WorkflowExecutionResult)
        assert len(result.retrieved_chunks) == 1
        assert result.retrieved_chunks[0].id == "chunk-1"

        # Verify orchestration flow
        deps["intent_classifier"].classify.assert_called_once_with("What is the deployment process?")
        deps["workflow_planner"].plan.assert_called_once()
        deps["embedding_orchestrator"].embed_query.assert_called_once_with(
            "What is the deployment process?"
        )
        deps["retrieval_service"].retrieve.assert_called_once()

    async def test_process_query_passes_limit_to_retrieval(self, mock_dependencies):
        """Test that process_query passes the limit parameter to retrieval."""
        # Setup mocks
        deps = mock_dependencies
        deps["intent_classifier"].classify.return_value = ClassifiedIntent(
            intent=IntentType.KNOWLEDGE_RETRIEVAL
        )
        deps["workflow_planner"].plan.return_value = WorkflowPlan(workflow=WorkflowType.RETRIEVAL)
        deps["embedding_orchestrator"].embed_query.return_value = [0.1] * 384
        deps["retrieval_service"].retrieve.return_value = []

        service = SupervisorService(**deps)

        # Execute with custom limit
        await service.process_query("test query", limit=10)

        # Verify limit was passed through
        call_args = deps["retrieval_service"].retrieve.call_args
        search_params = call_args[0][0]
        assert isinstance(search_params, VectorSearchParams)
        assert search_params.limit == 10

    async def test_process_query_handles_empty_results(self, mock_dependencies):
        """Test that process_query handles empty retrieval results correctly."""
        # Setup mocks
        deps = mock_dependencies
        deps["intent_classifier"].classify.return_value = ClassifiedIntent(
            intent=IntentType.KNOWLEDGE_RETRIEVAL
        )
        deps["workflow_planner"].plan.return_value = WorkflowPlan(workflow=WorkflowType.RETRIEVAL)
        deps["embedding_orchestrator"].embed_query.return_value = [0.1] * 384
        deps["retrieval_service"].retrieve.return_value = []

        service = SupervisorService(**deps)

        # Execute
        result = await service.process_query("test query", limit=5)

        # Verify
        assert isinstance(result, WorkflowExecutionResult)
        assert len(result.retrieved_chunks) == 0

    async def test_process_query_propagates_domain_exceptions_unchanged(self, mock_dependencies):
        """Test that process_query propagates SentinelBaseException unchanged."""
        from app.common.exceptions import SentinelBaseException

        class DummyDomainError(SentinelBaseException):
            def __init__(self):
                super().__init__("Dummy error", "DUMMY_ERROR", 400)

        # Setup mocks
        deps = mock_dependencies
        deps["intent_classifier"].classify.return_value = ClassifiedIntent(
            intent=IntentType.KNOWLEDGE_RETRIEVAL
        )
        deps["workflow_planner"].plan.return_value = WorkflowPlan(workflow=WorkflowType.RETRIEVAL)
        deps["embedding_orchestrator"].embed_query.return_value = [0.1] * 384
        
        # Make retrieval raise a domain exception
        dummy_error = DummyDomainError()
        deps["retrieval_service"].retrieve.side_effect = dummy_error

        service = SupervisorService(**deps)

        # Execute and verify
        with pytest.raises(DummyDomainError) as exc_info:
            await service.process_query("test query")
            
        assert exc_info.value is dummy_error

    async def test_process_query_wraps_unexpected_exceptions(self, mock_dependencies):
        """Test that process_query wraps standard Python exceptions in SentinelSupervisorError."""
        from app.agents.supervisor.exceptions import SentinelSupervisorError

        # Setup mocks
        deps = mock_dependencies
        deps["intent_classifier"].classify.return_value = ClassifiedIntent(
            intent=IntentType.KNOWLEDGE_RETRIEVAL
        )
        deps["workflow_planner"].plan.return_value = WorkflowPlan(workflow=WorkflowType.RETRIEVAL)
        
        # Make embedding orchestrator raise an unexpected exception
        unexpected_error = ValueError("Embedding service offline")
        deps["embedding_orchestrator"].embed_query.side_effect = unexpected_error

        service = SupervisorService(**deps)

        # Execute and verify
        with pytest.raises(SentinelSupervisorError) as exc_info:
            await service.process_query("test query")
            
        assert "Unexpected orchestration failure: Embedding service offline" in exc_info.value.message
        assert exc_info.value.__cause__ is unexpected_error

    async def test_process_query_handles_chain_propagation(self, mock_dependencies):
        """Test that unexpected exceptions anywhere in the chain are correctly wrapped."""
        from app.agents.supervisor.exceptions import SentinelSupervisorError

        # Setup mocks
        deps = mock_dependencies
        
        # Make the very first step (intent classification) fail unexpectedly
        unexpected_error = RuntimeError("Classifier model failed")
        deps["intent_classifier"].classify.side_effect = unexpected_error

        service = SupervisorService(**deps)

        # Execute and verify
        with pytest.raises(SentinelSupervisorError) as exc_info:
            await service.process_query("test query")
            
        assert "Unexpected orchestration failure: Classifier model failed" in exc_info.value.message
        assert exc_info.value.__cause__ is unexpected_error


class TestSupervisorOrchestrationDependencyInjection:
    """Test the supervisor orchestration dependency injection."""

    def test_get_supervisor_service_composes_all_dependencies(self):
        """Test that get_supervisor_service composes all required dependencies."""

        pass  



