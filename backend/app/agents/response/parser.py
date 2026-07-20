"""Response Parser for translating LLM provider output into the domain contract."""

from app.agents.response.models import GeneratedResponse, LLMResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseParser:
    """Parses raw LLM responses into the public GeneratedResponse contract."""

    def parse(self, llm_response: LLMResponse) -> GeneratedResponse:
        """Transforms an internal LLMResponse into the public GeneratedResponse."""
        logger.debug(
            "Parsing LLM response into GeneratedResponse.",
            extra={"raw_length": len(llm_response.text)}
        )
        
        return GeneratedResponse(content=llm_response.text.strip())
