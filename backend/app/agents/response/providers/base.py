"""Base interface for LLM providers."""

from abc import ABC, abstractmethod

from app.agents.response.models import LLMResponse, Prompt


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: Prompt) -> LLMResponse:
        """Generates raw text from the LLM given a provider-agnostic prompt."""
        pass
