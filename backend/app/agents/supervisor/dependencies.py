"""FastAPI dependency injection for the supervisor service."""

from typing import Annotated

from fastapi import Depends

from app.agents.supervisor.classifier import IntentClassifier
from app.agents.supervisor.planner import WorkflowPlanner
from app.agents.supervisor.service import SupervisorService
from app.config.settings import Settings, get_settings
from app.llms.embeddings.factory import get_embedding_provider
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator
from app.modules.retrieval.dependencies import get_retrieval_service
from app.modules.retrieval.service import RetrievalService


def get_intent_classifier() -> IntentClassifier:
    """Create and return an IntentClassifier instance.

    Returns:
        Fully initialized IntentClassifier instance.
    """
    return IntentClassifier()


def get_workflow_planner() -> WorkflowPlanner:
    """Create and return a WorkflowPlanner instance.

    Returns:
        Fully initialized WorkflowPlanner instance.
    """
    return WorkflowPlanner()


def get_embedding_orchestrator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> EmbeddingOrchestrator:
    """Create and return an EmbeddingOrchestrator instance.

    Returns:
        Fully initialized EmbeddingOrchestrator instance.
    """
    provider = get_embedding_provider(settings)
    return EmbeddingOrchestrator(
        provider=provider,
        batch_size=settings.embedding_batch_size,
    )


def get_supervisor_service(
    intent_classifier: Annotated[IntentClassifier, Depends(get_intent_classifier)],
    workflow_planner: Annotated[WorkflowPlanner, Depends(get_workflow_planner)],
    embedding_orchestrator: Annotated[EmbeddingOrchestrator, Depends(get_embedding_orchestrator)],
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SupervisorService:
    """Create and return a SupervisorService with all injected dependencies.

    Returns:
        Fully initialized SupervisorService instance.
    """
    return SupervisorService(
        intent_classifier=intent_classifier,
        workflow_planner=workflow_planner,
        embedding_orchestrator=embedding_orchestrator,
        retrieval_service=retrieval_service,
        settings=settings,
    )
