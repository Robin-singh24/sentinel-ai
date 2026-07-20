"""Unit tests for the Grok Provider."""

from unittest.mock import Mock, patch

import pytest
from app.agents.response.models import LLMResponse, Prompt
from app.agents.response.providers.grok import GrokProvider
from app.common.exceptions import SentinelProviderError
from httpx import HTTPStatusError, RequestError


@pytest.fixture
def valid_prompt():
    return Prompt(system_prompt="System", user_prompt="User")


@pytest.fixture
def provider():
    return GrokProvider(api_key="test-key", model="test-model")


class TestGrokProvider:
    """Tests for the GrokProvider implementation."""

    @pytest.mark.asyncio
    async def test_generate_success(self, provider, valid_prompt):
        """Verify successful LLM generation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated text."}}]
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await provider.generate(valid_prompt)

            assert isinstance(result, LLMResponse)
            assert result.text == "Generated text."

            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            
            assert kwargs["headers"]["Authorization"] == "Bearer test-key"
            assert kwargs["json"]["model"] == "test-model"
            assert kwargs["json"]["messages"][0]["content"] == "System"
            assert kwargs["json"]["messages"][1]["content"] == "User"

    @pytest.mark.asyncio
    async def test_generate_missing_api_key(self, valid_prompt):
        """Verify error when API key is missing."""
        provider = GrokProvider(api_key="")
        
        with pytest.raises(SentinelProviderError, match="API key is missing"):
            await provider.generate(valid_prompt)

    @pytest.mark.asyncio
    async def test_generate_http_error(self, provider, valid_prompt):
        """Verify HTTP errors are wrapped correctly."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        error = HTTPStatusError("Error", request=Mock(), response=mock_response)
        
        with patch("httpx.AsyncClient.post", side_effect=error):
            with pytest.raises(SentinelProviderError, match="Grok API error: 500"):
                await provider.generate(valid_prompt)

    @pytest.mark.asyncio
    async def test_generate_request_error(self, provider, valid_prompt):
        """Verify network errors are wrapped correctly."""
        error = RequestError("Network error", request=Mock())
        
        with patch("httpx.AsyncClient.post", side_effect=error):
            with pytest.raises(SentinelProviderError, match="Failed to generate response"):
                await provider.generate(valid_prompt)

    @pytest.mark.asyncio
    async def test_generate_invalid_response_format(self, provider, valid_prompt):
        """Verify invalid JSON formats are handled."""
        mock_response = Mock()
        # Missing 'choices'
        mock_response.json.return_value = {"invalid": "format"}

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(SentinelProviderError, match="Failed to generate response"):
                await provider.generate(valid_prompt)
