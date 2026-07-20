"""Integration tests for the Response Agent pipeline."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from app.agents.response.exceptions import SentinelResponseError
from app.agents.response.formatter import ContextFormatter
from app.agents.response.models import GeneratedResponse, LLMResponse, Prompt
from app.agents.response.parser import ResponseParser
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.prompt_templates import SYSTEM_PROMPT
from app.agents.response.providers.base import BaseLLMProvider
from app.agents.response.service import ResponseService
from app.agents.supervisor.models import WorkflowExecutionResult
from app.common.exceptions import SentinelProviderError
from app.vectorstore.repositories.models import VectorSearchResult


class FailingTestParser(ResponseParser):
    """Test-only parser that predictably fails to verify error propagation."""
    def parse(self, llm_response: LLMResponse) -> GeneratedResponse:
        raise SentinelResponseError("Simulated parsing failure.")


@pytest.fixture
def formatter():
    return ContextFormatter()


@pytest.fixture
def prompt_builder():
    return PromptBuilder()


@pytest.fixture
def parser():
    return ResponseParser()


@pytest.fixture
def mock_provider():
    provider = AsyncMock(spec=BaseLLMProvider)
    # Default successful return
    provider.generate.return_value = LLMResponse(text="Mocked generated text.")
    return provider


@pytest.fixture
def service(formatter, prompt_builder, parser, mock_provider):
    return ResponseService(
        formatter=formatter,
        prompt_builder=prompt_builder,
        llm_provider=mock_provider,
        parser=parser,
    )


class TestResponseAgentIntegration:
    """Integration test suite for the complete Response Agent pipeline."""

    @pytest.mark.asyncio
    async def test_successful_end_to_end_generation(self, service, mock_provider):
        """Verify the complete pipeline works with a valid context."""
        chunk = VectorSearchResult(
            id="1",
            score=0.9,
            payload={"text": "Python is a programming language.", "source": "doc1.txt"}
        )
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[chunk])
        query = "What is Python?"

        result = await service.generate_response(query=query, workflow_result=workflow_result)

        # Verify final output
        assert isinstance(result, GeneratedResponse)
        assert result.content == "Mocked generated text."

        # Verify prompt construction (Observable behavior)
        mock_provider.generate.assert_called_once()
        prompt_arg = mock_provider.generate.call_args[0][0]
        assert isinstance(prompt_arg, Prompt)
        
        # Verify strict prompt contents
        assert prompt_arg.system_prompt == SYSTEM_PROMPT
        assert query in prompt_arg.user_prompt
        assert "Python is a programming language." in prompt_arg.user_prompt
        # Context appears exactly once
        assert prompt_arg.user_prompt.count("Python is a programming language.") == 1

    @pytest.mark.asyncio
    async def test_empty_retrieval_context(self, service, mock_provider):
        """Verify pipeline handles an empty retrieval context gracefully."""
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[])
        query = "What is Python?"

        result = await service.generate_response(query=query, workflow_result=workflow_result)

        assert isinstance(result, GeneratedResponse)
        assert result.content == "Mocked generated text."

        # Verify empty context prompt formatting
        prompt_arg = mock_provider.generate.call_args[0][0]
        assert query in prompt_arg.user_prompt
        # The user prompt should have an empty context block
        assert "Context:\n\n\n\nUser Question:" in prompt_arg.user_prompt

    @pytest.mark.asyncio
    async def test_multi_document_retrieval_context(self, service, mock_provider):
        """Verify multi-document contexts are assembled and ordering is preserved."""
        chunk1 = VectorSearchResult(
            id="1", score=0.9, payload={"text": "First detail.", "source": "A.pdf"}
        )
        chunk2 = VectorSearchResult(
            id="2", score=0.8, payload={"text": "Second detail.", "source": "B.pdf"}
        )
        chunk3 = VectorSearchResult(
            id="3", score=0.7, payload={"text": "Third detail.", "source": "C.pdf"}
        )
        
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[chunk1, chunk2, chunk3])
        query = "Summarize the details."

        await service.generate_response(query=query, workflow_result=workflow_result)

        prompt_arg = mock_provider.generate.call_args[0][0]
        prompt_text = prompt_arg.user_prompt
        
        # All details must be included
        assert "First detail." in prompt_text
        assert "Second detail." in prompt_text
        assert "Third detail." in prompt_text
        
        # Ordering must be strictly preserved
        pos1 = prompt_text.find("First detail.")
        pos2 = prompt_text.find("Second detail.")
        pos3 = prompt_text.find("Third detail.")
        assert pos1 < pos2 < pos3, "Context ordering was not preserved."

    @pytest.mark.asyncio
    async def test_provider_failure_propagation(self, service, mock_provider):
        """Verify SentinelProviderError propagates unchanged."""
        mock_provider.generate.side_effect = SentinelProviderError("Network timeout")
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[])
        
        with pytest.raises(SentinelProviderError, match="Network timeout"):
            await service.generate_response(query="test", workflow_result=workflow_result)

    @pytest.mark.asyncio
    async def test_parser_failure_propagation(self, formatter, prompt_builder, mock_provider):
        """Verify parser errors propagate unchanged using a real (test-only) failing component."""
        failing_parser = FailingTestParser()
        service = ResponseService(
            formatter=formatter,
            prompt_builder=prompt_builder,
            llm_provider=mock_provider,
            parser=failing_parser,
        )
        
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[])
        
        with pytest.raises(SentinelResponseError, match="Simulated parsing failure."):
            await service.generate_response(query="test", workflow_result=workflow_result)

    @pytest.mark.asyncio
    async def test_unexpected_exception_wrapping(self, service, mock_provider):
        """Verify unexpected implementation errors are caught and wrapped securely."""
        # Sabotage the provider to throw a random ValueError
        mock_provider.generate.side_effect = ValueError("Something internal exploded")
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[])
        
        with pytest.raises(
            SentinelResponseError, 
            match="Unexpected error occurred during response generation."
        ) as exc_info:
            await service.generate_response(query="test", workflow_result=workflow_result)
            
        # Verify the original exception is preserved as the cause
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "Something internal exploded"

    @pytest.mark.asyncio
    async def test_cancellation_propagation(self, service, mock_provider):
        """Verify asyncio.CancelledError passes through completely untouched."""
        mock_provider.generate.side_effect = asyncio.CancelledError()
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[])
        
        with pytest.raises(asyncio.CancelledError):
            await service.generate_response(query="test", workflow_result=workflow_result)
