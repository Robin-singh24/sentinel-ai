"""Base interface for all embedding providers."""

from abc import ABC, abstractmethod

from app.llms.embeddings.models import EmbeddingRequest, EmbeddingResponse


class BaseEmbeddingProvider(ABC):
    """
    Abstract base class for all embedding providers.

    All specific implementations (e.g. BGE-M3, OpenAI, Groq) must inherit
    from this class and implement the `embed` method.
    """

    @abstractmethod
    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings for a list of texts.

        Args:
            request: The request containing text strings to embed.

        Returns:
            The embedding response containing vectors and metadata.

        Raises:
            SentinelProviderError: If the underlying model or API fails.
            SentinelValidationError: If the input request is invalid.
        """
        pass
