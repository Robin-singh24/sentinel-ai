"""Grok LLM Provider implementation."""

import httpx
from httpx import HTTPStatusError, RequestError

from app.agents.response.models import LLMResponse, Prompt
from app.agents.response.providers.base import BaseLLMProvider
from app.common.exceptions import SentinelProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class GrokProvider(BaseLLMProvider):
    """Concrete implementation for the Grok LLM API via xAI."""

    def __init__(self, api_key: str, model: str = "grok-beta") -> None:
        """Initialize the Grok provider."""
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.x.ai/v1/chat/completions"

    async def generate(self, prompt: Prompt) -> LLMResponse:
        """Generates text using the Grok API."""
        logger.debug(
            "Calling Grok API.",
            extra={"model": self.model, "prompt_length": len(prompt.user_prompt)}
        )

        if not self.api_key:
            raise SentinelProviderError("Grok API key is missing or empty.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            "temperature": 0.0,  # Deterministic output for RAG
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                return LLMResponse(text=content)

        except HTTPStatusError as e:
            logger.error(
                "Grok API returned an error status.",
                extra={"status_code": e.response.status_code, "response": e.response.text}
            )
            raise SentinelProviderError(f"Grok API error: {e.response.status_code}") from e
        except (RequestError, KeyError, IndexError, ValueError) as e:
            logger.error("Failed to communicate with Grok API or parse response.", exc_info=True)
            raise SentinelProviderError(f"Failed to generate response: {e!s}") from e
