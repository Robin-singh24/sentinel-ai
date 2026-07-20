"""Prompt Builder for the Response Agent."""

from app.agents.response.models import FormattedContext, Prompt
from app.agents.response.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """Assembles the final provider-agnostic prompt.
    
    Combines the raw user query with the structured FormattedContext,
    utilizing centralized templates for consistency.
    """

    def build(self, query: str, context: FormattedContext) -> Prompt:
        """Constructs a deterministic prompt from the query and context.
        
        Args:
            query: The original user query.
            context: The deterministic formatted context representation.
            
        Returns:
            Prompt: The structured prompt components ready for LLM consumption.
        """
        logger.debug(
            "Building prompt.",
            extra={
                "query_length": len(query),
                "context_length": len(context.text),
            },
        )
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context.text,
            query=query
        )
        
        return Prompt(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
