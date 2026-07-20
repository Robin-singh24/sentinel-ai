"""Intent classifier for the supervisor."""

from app.agents.supervisor.models import ClassifiedIntent, IntentType


class IntentClassifier:
    """Classifies user queries into workflow categories."""

    def classify(self, query: str) -> ClassifiedIntent:
        """
            Classify a user query into a workflow category.
            Classification Rules:
                - Non-empty query → KNOWLEDGE_RETRIEVAL
                - Empty or whitespace-only → UNKNOWN
        """
        if query.strip():
            return ClassifiedIntent(intent=IntentType.KNOWLEDGE_RETRIEVAL)
        else:
            return ClassifiedIntent(intent=IntentType.UNKNOWN)
