"""
Embedding Provider Abstraction layer.

This package provides a provider-independent interface for generating text embeddings.
"""

from app.llms.embeddings.base import BaseEmbeddingProvider
from app.llms.embeddings.factory import get_embedding_provider
from app.llms.embeddings.models import EmbeddedChunk, EmbeddingRequest, EmbeddingResponse
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator

__all__ = [
    "BaseEmbeddingProvider",
    "get_embedding_provider",
    "EmbeddedChunk",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingOrchestrator",
]
