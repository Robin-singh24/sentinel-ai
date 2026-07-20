"""Response Agent Service."""
import asyncio
import uuid

from app.agents.response.exceptions import SentinelResponseError
from app.agents.response.formatter import ContextFormatter
from app.agents.response.models import GeneratedResponse
from app.agents.response.parser import ResponseParser
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.providers.base import BaseLLMProvider
from app.agents.supervisor.models import WorkflowExecutionResult
from app.common.exceptions import SentinelProviderError
from app.core.logging import get_logger
from app.modules.memory.formatter import FormattedMemory, MemoryFormatter
from app.modules.memory.service import ConversationMemoryService

logger = get_logger(__name__)


class ResponseService:
    """Service for generating responses from orchestrated knowledge."""
    
    def __init__(
        self,
        formatter: ContextFormatter,
        prompt_builder: PromptBuilder,
        llm_provider: BaseLLMProvider,
        parser: ResponseParser,
        memory_service: ConversationMemoryService,
        memory_formatter: MemoryFormatter,
    ) -> None:
        """Initialize the ResponseService with required dependencies."""
        self._formatter = formatter
        self._prompt_builder = prompt_builder
        self._llm_provider = llm_provider
        self._parser = parser
        self._memory_service = memory_service
        self._memory_formatter = memory_formatter

    async def generate_response(
        self,
        query: str,
        workflow_result: WorkflowExecutionResult,
        conversation_id: uuid.UUID | None = None,
    ) -> GeneratedResponse:
        """Generate a final response based on the user query, context, and optional memory."""
        logger.debug(
            "Generating response.",
            extra={
                "query_length": len(query),
                "chunks_count": len(workflow_result.retrieved_chunks),
                "conversation_id": str(conversation_id) if conversation_id else None,
            },
        )
        
        try:
            # 1. Fetch and format conversation memory (if requested)
            if conversation_id:
                raw_memory = await self._memory_service.get_memory(conversation_id)
                formatted_memory = self._memory_formatter.format(raw_memory)
            else:
                formatted_memory = FormattedMemory(memory="")

            # 2. Format context
            formatted_context = self._formatter.format(workflow_result)
            
            # 3. Build prompt
            prompt = self._prompt_builder.build(
                query=query, 
                context=formatted_context,
                memory=formatted_memory
            )
            
            # 3. Generate text from LLM provider
            llm_response = await self._llm_provider.generate(prompt)
            
            # 4. Parse the LLM response into the final GeneratedResponse
            return self._parser.parse(llm_response)
            
        except asyncio.CancelledError:
            logger.warning("Response generation cancelled by user/system.")
            raise
        except SentinelResponseError:
            # Re-raise known domain errors (e.g., from parser)
            raise
        except SentinelProviderError:
            # Re-raise known provider errors
            raise
        except Exception as e:
            logger.error("Unexpected error during response generation.", exc_info=True)
            raise SentinelResponseError(
                "Unexpected error occurred during response generation."
            ) from e
