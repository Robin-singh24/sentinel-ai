"""Unit tests for the Response Parser."""

from app.agents.response.models import GeneratedResponse, LLMResponse
from app.agents.response.parser import ResponseParser


class TestResponseParser:
    """Tests for the ResponseParser component."""

    def test_parse_valid_response(self):
        """Verify the parser successfully maps the raw text into the domain contract."""
        parser = ResponseParser()
        raw_text = "  This is a generated response.  \n"
        llm_response = LLMResponse(text=raw_text)
        
        result = parser.parse(llm_response)
        
        assert isinstance(result, GeneratedResponse)
        # Verify it strips the whitespace
        assert result.content == "This is a generated response."
