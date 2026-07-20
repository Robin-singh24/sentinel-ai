"""Intent classification tests for the supervisor module.

These tests validate the intent classifier's ability to categorize user queries
into workflow categories.
"""

import pytest

from app.agents.supervisor.classifier import IntentClassifier
from app.agents.supervisor.dependencies import get_intent_classifier
from app.agents.supervisor.models import ClassifiedIntent, IntentType


class TestIntentClassifier:
    """Test the IntentClassifier logic."""

    def test_non_empty_query_classified_as_knowledge_retrieval(self):
        """Test that any non-empty query is classified as KNOWLEDGE_RETRIEVAL."""
        classifier = IntentClassifier()
        
        queries = [
            "What is the deployment process?",
            "How do I configure the service?",
            "hello",
            "x",
            "Show me documentation",
        ]
        
        for query in queries:
            result = classifier.classify(query)
            assert isinstance(result, ClassifiedIntent)
            assert result.intent == IntentType.KNOWLEDGE_RETRIEVAL

    def test_empty_query_classified_as_unknown(self):
        """Test that empty queries are classified as UNKNOWN."""
        classifier = IntentClassifier()
        
        result = classifier.classify("")
        assert isinstance(result, ClassifiedIntent)
        assert result.intent == IntentType.UNKNOWN

    def test_whitespace_only_query_classified_as_unknown(self):
        """Test that whitespace-only queries are classified as UNKNOWN."""
        classifier = IntentClassifier()
        
        whitespace_queries = [
            " ",
            "   ",
            "\t",
            "\n",
            "  \t  \n  ",
        ]
        
        for query in whitespace_queries:
            result = classifier.classify(query)
            assert isinstance(result, ClassifiedIntent)
            assert result.intent == IntentType.UNKNOWN

    def test_query_with_leading_trailing_whitespace(self):
        """Test that queries with surrounding whitespace are classified correctly."""
        classifier = IntentClassifier()
        
        result = classifier.classify("  What is this?  ")
        assert result.intent == IntentType.KNOWLEDGE_RETRIEVAL

    def test_classified_intent_is_frozen(self):
        """Test that ClassifiedIntent is immutable."""
        classifier = IntentClassifier()
        result = classifier.classify("test query")
        
        with pytest.raises(AttributeError):
            result.intent = IntentType.UNKNOWN  # type: ignore


class TestIntentClassifierDependencyInjection:
    """Test the intent classifier dependency injection."""

    def test_get_intent_classifier_returns_instance(self):
        """Test that get_intent_classifier returns an IntentClassifier instance."""
        classifier = get_intent_classifier()
        assert isinstance(classifier, IntentClassifier)

    def test_get_intent_classifier_creates_new_instance(self):
        """Test that get_intent_classifier creates a new instance each time."""
        classifier1 = get_intent_classifier()
        classifier2 = get_intent_classifier()
        assert classifier1 is not classifier2

    def test_classifier_from_di_works_correctly(self):
        """Test that classifier obtained via DI works as expected."""
        classifier = get_intent_classifier()
        result = classifier.classify("Test query")
        assert result.intent == IntentType.KNOWLEDGE_RETRIEVAL
