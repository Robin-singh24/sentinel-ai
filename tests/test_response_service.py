"""Unit tests for the Response Service."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from app.agents.response.exceptions import SentinelResponseError
from app.agents.response.formatter import ContextFormatter
from app.agents.response.models import FormattedContext, GeneratedResponse, LLMResponse, Prompt
from app.agents.response.parser import ResponseParser
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.providers.base import BaseLLMProvider
from app.agents.response.service import ResponseService
from app.agents.supervisor.models import WorkflowExecutionResult
from app.common.exceptions import SentinelProviderError


class MockProvider(BaseLLMProvider):
    async def generate(self, prompt: Prompt) -> LLMResponse:
        return LLMResponse(text="Mocked output")


class TestResponseService:
    """Tests for the ResponseService orchestration."""

    @pytest.mark.asyncio
    async def test_generate_response_orchestrates_flow_and_returns_generated_response(self):
        """Verify the service calls formatting, building, provider, and parser."""
        mock_formatter = Mock(spec=ContextFormatter)
        mock_formatter.format.return_value = FormattedContext(text="Context")
        
        mock_builder = Mock(spec=PromptBuilder)
        mock_builder.build.return_value = Prompt(system_prompt="sys", user_prompt="usr")
        
        mock_provider = AsyncMock(spec=BaseLLMProvider)
        mock_provider.generate.return_value = LLMResponse(text="Final LLM text")
        
        mock_parser = Mock(spec=ResponseParser)
        mock_parser.parse.return_value = GeneratedResponse(content="Final Parsed Response")
        
        service = ResponseService(
            formatter=mock_formatter,
            prompt_builder=mock_builder,
            llm_provider=mock_provider,
            parser=mock_parser,
        )
        
        workflow_result = WorkflowExecutionResult(retrieved_chunks=[])
        query = "Test query"
        
        result = await service.generate_response(query=query, workflow_result=workflow_result)
        
        assert isinstance(result, GeneratedResponse)
        assert result.content == "Final Parsed Response"
            
        mock_formatter.format.assert_called_once_with(workflow_result)
        mock_builder.build.assert_called_once_with(
            query=query, 
            context=FormattedContext(text="Context")
        )
        mock_provider.generate.assert_called_once_with(
            Prompt(system_prompt="sys", user_prompt="usr")
        )

    @pytest.mark.asyncio
    async def test_generate_response_propagates_cancelled_error(self):
        """Verify asyncio.CancelledError is re-raised."""
        mock_formatter = Mock(spec=ContextFormatter)
        mock_formatter.format.side_effect = asyncio.CancelledError()
        
        service = ResponseService(
            formatter=mock_formatter,
            prompt_builder=Mock(spec=PromptBuilder),
            llm_provider=AsyncMock(spec=BaseLLMProvider),
            parser=Mock(spec=ResponseParser),
        )
        
        with pytest.raises(asyncio.CancelledError):
            await service.generate_response("q", WorkflowExecutionResult([]))

    @pytest.mark.asyncio
    async def test_generate_response_propagates_provider_error(self):
        """Verify SentinelProviderError is re-raised unchanged."""
        mock_formatter = Mock(spec=ContextFormatter)
        mock_formatter.format.return_value = FormattedContext("C")
        
        mock_builder = Mock(spec=PromptBuilder)
        mock_builder.build.return_value = Prompt("S", "U")
        
        mock_provider = AsyncMock(spec=BaseLLMProvider)
        mock_provider.generate.side_effect = SentinelProviderError("Provider failed")
        
        service = ResponseService(
            formatter=mock_formatter,
            prompt_builder=mock_builder,
            llm_provider=mock_provider,
            parser=Mock(spec=ResponseParser),
        )
        
        with pytest.raises(SentinelProviderError, match="Provider failed"):
            await service.generate_response("q", WorkflowExecutionResult([]))

    @pytest.mark.asyncio
    async def test_generate_response_propagates_response_error(self):
        """Verify SentinelResponseError is re-raised unchanged."""
        mock_formatter = Mock(spec=ContextFormatter)
        mock_formatter.format.side_effect = SentinelResponseError("Parse error")
        
        service = ResponseService(
            formatter=mock_formatter,
            prompt_builder=Mock(spec=PromptBuilder),
            llm_provider=AsyncMock(spec=BaseLLMProvider),
            parser=Mock(spec=ResponseParser),
        )
        
        with pytest.raises(SentinelResponseError, match="Parse error"):
            await service.generate_response("q", WorkflowExecutionResult([]))
            
    @pytest.mark.asyncio
    async def test_generate_response_wraps_unexpected_error(self):
        """Verify unexpected errors are wrapped in SentinelResponseError."""
        mock_formatter = Mock(spec=ContextFormatter)
        mock_formatter.format.side_effect = ValueError("Unexpected issue")
        
        service = ResponseService(
            formatter=mock_formatter,
            prompt_builder=Mock(spec=PromptBuilder),
            llm_provider=AsyncMock(spec=BaseLLMProvider),
            parser=Mock(spec=ResponseParser),
        )
        
        with pytest.raises(
            SentinelResponseError, 
            match="Unexpected error occurred during response generation."
        ):
            await service.generate_response("q", WorkflowExecutionResult([]))
