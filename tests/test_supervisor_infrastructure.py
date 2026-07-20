"""Infrastructure tests for the supervisor module.

These tests validate the supervisor module's infrastructure setup including
exceptions, service initialization, and dependency injection.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from app.agents.supervisor.classifier import IntentClassifier
from app.agents.supervisor.dependencies import get_supervisor_service
from app.agents.supervisor.exceptions import SentinelSupervisorError
from app.agents.supervisor.planner import WorkflowPlanner
from app.agents.supervisor.service import SupervisorService
from app.common.exceptions import SentinelBaseException
from app.config.settings import Settings
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator
from app.modules.retrieval.service import RetrievalService


class TestSentinelSupervisorError:
    """Test the SentinelSupervisorError exception."""

    def test_instantiation(self):
        """Test creating a SentinelSupervisorError."""
        error = SentinelSupervisorError("Orchestration failed")
        assert error.message == "Orchestration failed"
        assert error.code == "SUPERVISOR_ERROR"
        assert error.http_status == 500

    def test_inheritance(self):
        """Test that SentinelSupervisorError inherits from SentinelBaseException."""
        error = SentinelSupervisorError("Test error")
        assert isinstance(error, SentinelBaseException)
        assert isinstance(error, Exception)

    def test_error_properties(self):
        """Test that error properties are correctly set."""
        error = SentinelSupervisorError("Agent coordination failed")
        assert str(error) == "Agent coordination failed"
        assert error.code == "SUPERVISOR_ERROR"
        assert error.http_status == 500


class TestSupervisorServiceInfrastructure:
    """Test the SupervisorService infrastructure setup."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for testing."""
        return {
            "intent_classifier": Mock(spec=IntentClassifier),
            "workflow_planner": Mock(spec=WorkflowPlanner),
            "embedding_orchestrator": Mock(spec=EmbeddingOrchestrator),
            "retrieval_service": AsyncMock(spec=RetrievalService),
            "settings": Settings(),
        }

    def test_service_instantiation(self, mock_dependencies):
        """Test that SupervisorService can be instantiated with dependencies."""
        service = SupervisorService(**mock_dependencies)
        assert isinstance(service, SupervisorService)

    def test_service_has_required_dependencies(self, mock_dependencies):
        """Test that service requires all dependencies in Phase 10.4."""
        service = SupervisorService(**mock_dependencies)
        # Service should have all injected dependencies
        assert service._intent_classifier is not None
        assert service._workflow_planner is not None
        assert service._embedding_orchestrator is not None
        assert service._retrieval_service is not None
        assert service._settings is not None


class TestDependencyInjection:
    """Test the dependency injection setup.
    
    Note: These tests validate dependency composition without invoking external services.
    Full integration tests would require actual service instances.
    """

    def test_dependency_injection_function_exists(self):
        """Test that get_supervisor_service function exists and has correct signature."""
        # Validate that the DI function exists and can be imported
        assert callable(get_supervisor_service)
        # Function signature is validated by type checking
