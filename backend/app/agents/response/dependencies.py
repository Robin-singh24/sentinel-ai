"""FastAPI dependency injection for the response agent."""

from app.agents.response.formatter import ContextFormatter
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.service import ResponseService


def get_context_formatter() -> ContextFormatter:
    """Create and return a ContextFormatter instance."""
    return ContextFormatter()


def get_prompt_builder() -> PromptBuilder:
    """Create and return a PromptBuilder instance.
    
    Returns:
        Fully initialized PromptBuilder instance.
    """
    return PromptBuilder()


def get_response_service() -> ResponseService:
    """Create and return a ResponseService instance."""
    return ResponseService()
