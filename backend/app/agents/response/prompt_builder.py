"""Prompt Builder for the Response Agent."""

from app.agents.response.models import FormattedContext, Prompt
from app.agents.response.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.core.logging import get_logger
from app.modules.memory.formatter import FormattedMemory

logger = get_logger(__name__)


class PromptBuilder:
    """Assembles the final provider-agnostic prompt.
    
    Combines the raw user query with the structured FormattedContext,
    utilizing centralized templates for consistency.
    """

    def build(self, query: str, context: FormattedContext, memory: FormattedMemory) -> Prompt:
        """Constructs a deterministic prompt from the query, context, and memory.
        
        Args:
            query: The original user query.
            context: The deterministic formatted context representation.
            memory: The deterministic formatted conversation memory.
            
        Returns:
            Prompt: The structured prompt components ready for LLM consumption.
        """
        logger.debug(
            "Building prompt.",
            extra={
                "query_length": len(query),
                "context_length": len(context.text),
                "memory_length": len(memory.memory),
            },
        )
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            memory=memory.memory,
            context=context.text,
            query=query
        )
        
        return Prompt(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
