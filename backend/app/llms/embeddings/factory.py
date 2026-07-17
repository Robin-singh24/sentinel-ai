"""Factory for resolving and instantiating embedding providers."""

import logging
from typing import Dict, Type

from app.common.exceptions import SentinelProviderError
from app.config.settings import Settings
from app.llms.embeddings.base import BaseEmbeddingProvider
from app.llms.embeddings.providers.bge_m3 import BgeM3EmbeddingProvider

logger = logging.getLogger(__name__)

# Registry of supported providers mapping config values to class types
_PROVIDER_REGISTRY: Dict[str, Type[BaseEmbeddingProvider]] = {
    "bge_m3": BgeM3EmbeddingProvider,
}

def get_embedding_provider(settings: Settings) -> BaseEmbeddingProvider:
    """
    Factory function to get the configured embedding provider.

    Args:
        settings: Application settings containing provider and model configurations.

    Returns:
        An instance of a class implementing BaseEmbeddingProvider.

    Raises:
        SentinelProviderError: If the configured provider is not recognized.
    """
    provider_name = settings.embedding_provider.lower()

    if provider_name not in _PROVIDER_REGISTRY:
        logger.error(f"Unknown embedding provider requested: {provider_name}")
        raise SentinelProviderError(f"Unknown embedding provider: '{provider_name}'. Supported providers: {list(_PROVIDER_REGISTRY.keys())}")

    provider_class = _PROVIDER_REGISTRY[provider_name]
    logger.debug(f"Instantiating embedding provider: {provider_name} with model: {settings.embedding_model}")
    
    return provider_class(model_name=settings.embedding_model)
