"""BGE-M3 Provider implementation using Sentence Transformers."""

import logging
import time
from typing import Any

from app.common.exceptions import SentinelProviderError, SentinelValidationError
from app.llms.embeddings.base import BaseEmbeddingProvider
from app.llms.embeddings.models import EmbeddingRequest, EmbeddingResponse

logger = logging.getLogger(__name__)


class BgeM3EmbeddingProvider(BaseEmbeddingProvider):
    """
    Embedding provider for BAAI/bge-m3 using sentence-transformers.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self._model_name = model_name
        self._model: Any = None
        self._provider = "sentence-transformers"
        self._dimensions = 0

    def _load_model(self) -> None:
        """Lazily load the SentenceTransformer model."""
        if self._model is not None:
            return

        logger.info(f"Initializing embedding provider: {self._provider} with model {self._model_name}")
        start_time = time.perf_counter()
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dimensions = self._model.get_sentence_embedding_dimension()
        except ImportError as e:
            logger.error("Failed to import sentence-transformers.", exc_info=True)
            raise SentinelProviderError(
                "sentence-transformers is not installed. Please install it to use this provider."
            ) from e
        except Exception as e:
            logger.error(f"Failed to load model {self._model_name}: {e}", exc_info=True)
            raise SentinelProviderError(f"Failed to load embedding model: {e}") from e

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Model {self._model_name} loaded in {duration_ms:.2f}ms")

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings for a list of texts synchronously.
        """
        if not request.texts:
            raise SentinelValidationError("Embedding request must contain at least one text.", field="texts")

        self._load_model()
        
        logger.debug(f"Starting embedding generation for {len(request.texts)} chunks using {self._model_name}")
        start_time = time.perf_counter()

        try:
            # Generate embeddings (SentenceTransformers handles batching)
            embeddings_array = self._model.encode(request.texts)
            # Convert numpy array to list of lists of floats
            embeddings_list = embeddings_array.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
            raise SentinelProviderError(f"Embedding generation failed: {e}") from e

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Embedding generation completed in {duration_ms:.2f}ms")

        return EmbeddingResponse(
            embeddings=embeddings_list,
            dimensions=self._dimensions,
            provider=self._provider,
            model=self._model_name,
            processing_time_ms=duration_ms,
        )
