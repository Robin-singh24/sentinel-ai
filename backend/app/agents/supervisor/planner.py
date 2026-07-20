"""Workflow planner for the supervisor."""

from app.agents.supervisor.exceptions import SentinelSupervisorError
from app.agents.supervisor.models import ClassifiedIntent, IntentType, WorkflowPlan, WorkflowType


class WorkflowPlanner:
    """Plans workflow execution based on classified intent."""

    def plan(self, intent: ClassifiedIntent) -> WorkflowPlan:
        """Create an execution plan for the given intent.

        Planning Rules:
            - KNOWLEDGE_RETRIEVAL → RETRIEVAL workflow
            - UNKNOWN → Raises error (no valid workflow exists) """
        if intent.intent == IntentType.KNOWLEDGE_RETRIEVAL:
            return WorkflowPlan(workflow=WorkflowType.RETRIEVAL)
        elif intent.intent == IntentType.UNKNOWN:
            raise SentinelSupervisorError(
                "Cannot create workflow plan for UNKNOWN intent. "
                "The user query must be classified into a valid intent category."
            )
        else:
            # This branch should never be reached unless new intents are added
            raise SentinelSupervisorError(
                f"Unsupported intent type: {intent.intent}. "
                "No workflow mapping exists for this intent."
            )
