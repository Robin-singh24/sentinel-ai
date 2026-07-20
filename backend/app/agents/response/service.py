"""Response Agent Service."""


from app.agents.response.exceptions import SentinelResponseError
from app.agents.response.formatter import ContextFormatter
from app.agents.response.models import GeneratedResponse
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.providers.base import BaseLLMProvider
from app.agents.supervisor.models import WorkflowExecutionResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseService:
    """Service for generating responses from orchestrated knowledge."""
    
    def __init__(
        self,
        formatter: ContextFormatter,
        prompt_builder: PromptBuilder,
        llm_provider: BaseLLMProvider,
    ) -> None:
        """Initialize the ResponseService with required dependencies."""
        self._formatter = formatter
        self._prompt_builder = prompt_builder
        self._llm_provider = llm_provider

    async def generate_response(
        self,
        query: str,
        workflow_result: WorkflowExecutionResult,
    ) -> GeneratedResponse:
        """Generate a final response based on the user query and supervisor context."""
        logger.debug(
            "Generating response.",
            extra={
                "query_length": len(query),
                "chunks_count": len(workflow_result.retrieved_chunks),
            },
        )
        
        # 1. Format context
        formatted_context = self._formatter.format(workflow_result)
        
        # 2. Build prompt
        prompt = self._prompt_builder.build(query=query, context=formatted_context)
        
        # 3. Generate text from LLM provider
        await self._llm_provider.generate(prompt)
        
        # 4. Parsing is deferred to Phase 11.5
        # Stop here and raise SentinelResponseError as requested.
        raise SentinelResponseError("Response parsing is not yet implemented.")
