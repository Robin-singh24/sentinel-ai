"""Orchestrator for embedding generation workflows."""

import logging
import time
from typing import Iterator

from app.common.exceptions import SentinelProviderError, SentinelValidationError
from app.llms.embeddings.base import BaseEmbeddingProvider
from app.llms.embeddings.models import EmbeddedChunk, EmbeddingRequest, EmbeddingResponse
from app.modules.ingestion.metadata.models import ProcessedChunk

logger = logging.getLogger(__name__)


class EmbeddingOrchestrator:
    """
    Coordinates the generation of embeddings for processed document chunks in batches.
    
    This orchestrator acts as a bridge between the ingestion pipeline and the 
    underlying embedding providers, maintaining strict independence from the 
    specific model implementations.
    """

    def __init__(self, provider: BaseEmbeddingProvider, batch_size: int = 32):
        """
        Initialize the orchestrator with an injected embedding provider.
        
        Args:
            provider: An already constructed embedding provider instance.
            batch_size: The number of chunks to process in a single embedding request.
            
        Raises:
            SentinelValidationError: If batch_size is less than or equal to 0.
        """
        if batch_size <= 0:
            raise SentinelValidationError("Embedding batch size must be greater than 0.", field="batch_size")
            
        self._provider = provider
        self._batch_size = batch_size

    def _create_batches(self, chunks: list[ProcessedChunk], batch_size: int) -> Iterator[list[ProcessedChunk]]:
        """Yield sequential batches of ProcessedChunks."""
        for i in range(0, len(chunks), batch_size):
            yield chunks[i : i + batch_size]

    def _validate_embedding_response(
        self, 
        response: EmbeddingResponse, 
        expected_count: int, 
        locked_dimension: int | None
    ) -> int:
        """
        Validate a single batch response from the provider.
        
        Args:
            response: The EmbeddingResponse from the provider.
            expected_count: The number of input texts sent in this batch.
            locked_dimension: The dimension expected across all batches, if known.
            
        Returns:
            The validated dimension for this batch.
            
        Raises:
            SentinelProviderError: If the response fails any validation rules.
        """
        # 1. Provider returned the same number of vectors as chunks
        if len(response.embeddings) != expected_count:
            raise SentinelProviderError(
                f"Provider returned {len(response.embeddings)} embeddings, expected {expected_count}."
            )

        # 2. Response dimensions > 0
        if response.dimensions <= 0:
            raise SentinelProviderError("Provider returned invalid dimensions (<= 0).")

        # 3. First vector determines the expected dimension
        first_vector = response.embeddings[0]
        if not first_vector:
            raise SentinelProviderError("Provider returned an empty embedding vector.")
            
        current_dimension = len(first_vector)

        # Ensure it matches previously locked dimension across batches
        if locked_dimension is not None and current_dimension != locked_dimension:
            raise SentinelProviderError(
                f"Batch dimension mismatch. Expected {locked_dimension}, got {current_dimension}."
            )

        # 4. Every remaining vector matches that dimension
        for i, vector in enumerate(response.embeddings):
            if not vector:
                raise SentinelProviderError(f"Provider returned an empty vector at index {i}.")
            if len(vector) != current_dimension:
                raise SentinelProviderError(
                    f"Dimension mismatch at index {i}. Expected {current_dimension}, got {len(vector)}."
                )

        # 5. Response.dimensions equals the validated dimension
        if response.dimensions != current_dimension:
            raise SentinelProviderError(
                f"Response metadata dimension ({response.dimensions}) does not match vector dimension ({current_dimension})."
            )
            
        return current_dimension

    def embed(self, chunks: list[ProcessedChunk]) -> list[EmbeddedChunk]:
        """
        Generate embeddings for a collection of processed chunks using batching.

        Args:
            chunks: A list of immutable ProcessedChunk instances.

        Returns:
            A list of EmbeddedChunk instances containing vectors.

        Raises:
            SentinelValidationError: If the input list is empty.
            SentinelProviderError: If the provider fails or validation fails.
        """
        if not chunks:
            raise SentinelValidationError("Cannot embed an empty list of chunks.", field="chunks")

        total_chunks = len(chunks)
        total_batches = (total_chunks + self._batch_size - 1) // self._batch_size
        
        logger.info(f"Starting orchestration for {total_chunks} chunks in {total_batches} batches.")
        
        start_time = time.perf_counter()
        
        all_embedded_chunks = []
        locked_dimension: int | None = None
        
        # Track provider metadata for final logging
        provider_name = "unknown"
        model_name = "unknown"

        for batch_index, batch in enumerate(self._create_batches(chunks, self._batch_size), start=1):
            texts = [chunk.content for chunk in batch]
            request = EmbeddingRequest(texts=texts)

            # Invoke the provider synchronously
            response = self._provider.embed(request)
            
            # Store metadata dynamically from the first valid response
            if locked_dimension is None:
                provider_name = response.provider
                model_name = response.model

            # Validate the batch output
            locked_dimension = self._validate_embedding_response(
                response=response,
                expected_count=len(batch),
                locked_dimension=locked_dimension,
            )

            # Construct EmbeddedChunk objects for this batch
            for chunk, vector in zip(batch, response.embeddings):
                all_embedded_chunks.append(
                    EmbeddedChunk(chunk=chunk, vector=vector, dimensions=response.dimensions)
                )
                
            logger.debug(
                f"Completed batch {batch_index}/{total_batches} "
                f"(size: {len(batch)}) using provider '{provider_name}'."
            )

        # Final validation
        if len(all_embedded_chunks) != total_chunks:
            raise SentinelProviderError(
                f"Merged vector count ({len(all_embedded_chunks)}) does not match original chunk count ({total_chunks})."
            )

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Embedding orchestration completed successfully. Provider: {provider_name}, "
            f"Model: {model_name}, Batch Size: {self._batch_size}, "
            f"Total Batches: {total_batches}, Total Chunks: {total_chunks}, "
            f"Dimension: {locked_dimension}, Duration: {duration_ms:.2f}ms."
        )

        return all_embedded_chunks
