"""Unit tests for the Response Context Formatter."""

from app.agents.response.dependencies import get_context_formatter
from app.agents.response.formatter import ContextFormatter
from app.agents.response.models import FormattedContext
from app.agents.supervisor.models import WorkflowExecutionResult
from app.vectorstore.repositories.models import VectorSearchResult


class TestContextFormatter:
    """Tests for the ContextFormatter logic."""

    def test_format_preserves_order_and_content(self):
        """Verify that the formatter extracts text and preserves exact chunk ordering."""
        formatter = ContextFormatter()
        
        # Create dummy retrieved chunks in a specific order
        chunks = [
            VectorSearchResult(
                id="chunk-1", 
                score=0.9, 
                payload={"text": "First chunk text"},
                vector=None
            ),
            VectorSearchResult(
                id="chunk-2", 
                score=0.8, 
                payload={"content": "Second chunk text"}, # testing 'content' fallback
                vector=None
            ),
            VectorSearchResult(
                id="chunk-3", 
                score=0.7, 
                payload={"text": "Third chunk text"},
                vector=None
            ),
        ]
        
        workflow_result = WorkflowExecutionResult(retrieved_chunks=chunks)
        
        # Execute
        result = formatter.format(workflow_result)
        
        # Verify
        assert isinstance(result, FormattedContext)
        
        expected_text = (
            "[Context 1]\nFirst chunk text\n\n"
            "[Context 2]\nSecond chunk text\n\n"
            "[Context 3]\nThird chunk text"
        )
        assert result.text == expected_text

    def test_format_does_not_deduplicate_or_filter(self):
        """Verify that identical or low-score chunks are not dropped."""
        formatter = ContextFormatter()
        
        # Create chunks with identical payloads
        chunks = [
            VectorSearchResult(
                id="chunk-1", 
                score=0.9, 
                payload={"text": "Duplicate content"},
                vector=None
            ),
            VectorSearchResult(
                id="chunk-2", 
                score=0.1, # Extremely low score, but passed by supervisor
                payload={"text": "Duplicate content"},
                vector=None
            ),
        ]
        
        workflow_result = WorkflowExecutionResult(retrieved_chunks=chunks)
        
        # Execute
        result = formatter.format(workflow_result)
        
        # Verify
        assert isinstance(result, FormattedContext)
        
        expected_text = (
            "[Context 1]\nDuplicate content\n\n"
            "[Context 2]\nDuplicate content"
        )
        assert result.text == expected_text

    def test_format_handles_missing_text_fields(self):
        """Verify fallback behavior when exact text fields are missing."""
        formatter = ContextFormatter()
        
        chunks = [
            VectorSearchResult(
                id="chunk-1", 
                score=0.9, 
                payload={"some_other_field": "data value"},
                vector=None
            ),
            VectorSearchResult(
                id="chunk-2", 
                score=0.9, 
                payload={}, # Empty payload, should be skipped
                vector=None
            ),
        ]
        
        workflow_result = WorkflowExecutionResult(retrieved_chunks=chunks)
        result = formatter.format(workflow_result)
        
        # Should fallback to string representation of the dict for chunk 1
        assert "[Context 1]" in result.text
        assert "{'some_other_field': 'data value'}" in result.text
        # Chunk 2 should not result in a [Context 2] block because payload is empty
        assert "[Context 2]" not in result.text

    def test_format_handles_empty_results(self):
        """Verify behavior with zero retrieved chunks."""
        formatter = ContextFormatter()
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[])
        
        result = formatter.format(workflow_result)
        
        assert isinstance(result, FormattedContext)
        assert result.text == ""


class TestResponseDependencies:
    """Test response agent dependency injection."""
    
    def test_get_context_formatter(self):
        """Verify factory returns correct instance."""
        formatter = get_context_formatter()
        assert isinstance(formatter, ContextFormatter)
