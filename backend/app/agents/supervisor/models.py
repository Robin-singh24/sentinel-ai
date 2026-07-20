"""Intent classification models for the supervisor."""

import enum
from dataclasses import dataclass

from app.vectorstore.repositories.models import VectorSearchResult


class IntentType(str, enum.Enum):
    """Workflow categories that the Supervisor can execute."""

    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClassifiedIntent:
    """Result of intent classification."""
    intent: IntentType


class WorkflowType(str, enum.Enum):
    """Execution workflows that the Supervisor can orchestrate."""

    RETRIEVAL = "retrieval"


@dataclass(frozen=True)
class WorkflowPlan:
    """Execution plan produced by the workflow planner. """

    workflow: WorkflowType


@dataclass(frozen=True)
class WorkflowExecutionResult:
    """Result of workflow execution by the Supervisor."""

    retrieved_chunks: list[VectorSearchResult]
