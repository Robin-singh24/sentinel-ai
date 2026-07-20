"""FastAPI dependency injection for the response agent."""

from typing import Annotated

from fastapi import Depends

from app.agents.response.formatter import ContextFormatter
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.providers.base import BaseLLMProvider
from app.agents.response.providers.grok import GrokProvider
from app.agents.response.service import ResponseService
from app.config.settings import Settings, get_settings


def get_context_formatter() -> ContextFormatter:
    """Create and return a ContextFormatter instance."""
    return ContextFormatter()


def get_prompt_builder() -> PromptBuilder:
    """Create and return a PromptBuilder instance.
    
    Returns:
        Fully initialized PromptBuilder instance.
    """
    return PromptBuilder()


def get_llm_provider(settings: Annotated[Settings, Depends(get_settings)]) -> BaseLLMProvider:
    """Create and return the LLM provider instance based on settings.
    
    Returns:
        Fully initialized BaseLLMProvider implementation (GrokProvider).
    """
    return GrokProvider(api_key=settings.grok_api_key, model=settings.llm_model)


def get_response_service(
    formatter: Annotated[ContextFormatter, Depends(get_context_formatter)],
    prompt_builder: Annotated[PromptBuilder, Depends(get_prompt_builder)],
    llm_provider: Annotated[BaseLLMProvider, Depends(get_llm_provider)],
) -> ResponseService:
    """Create and return a ResponseService instance."""
    return ResponseService(
        formatter=formatter,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
    )
