"""Retrieval service — orchestrates vector similarity search operations."""

from app.modules.retrieval.exceptions import SentinelRetrievalError
from app.vectorstore.exceptions import SentinelVectorStoreError
from app.vectorstore.repositories.models import VectorSearchParams, VectorSearchResult
from app.vectorstore.repositories.repository import VectorRepository


class RetrievalService:
    """Generic retrieval service for vector similarity search.

    This service wraps VectorRepository operations with retrieval-specific
    error handling. It remains domain-agnostic and treats payloads as
    opaque dictionaries.

    The service expects callers to:
    - Generate query embeddings upstream
    - Interpret payload semantics
    - Apply business-specific filtering

    Logging is handled by VectorRepository to avoid duplication.
    """

    def __init__(
        self,
        vector_repository: VectorRepository,
    ) -> None:
        self._vector_repo = vector_repository

    async def retrieve(
        self,
        params: VectorSearchParams,
    ) -> list[VectorSearchResult]:
        """Execute vector similarity search against the specified collection.

        This method delegates to VectorRepository and wraps infrastructure
        exceptions with retrieval-specific error types.

        Args:
            params: Vector search parameters including query vector, limit,
                   score threshold, and metadata filters.

        Returns:
            List of VectorSearchResult objects with scores and payloads.

        Raises:
            SentinelRetrievalError: If the retrieval operation fails.
        """
        try:
            return await self._vector_repo.search(params)
        except SentinelVectorStoreError as e:
            raise SentinelRetrievalError(
                f"Failed to retrieve from collection '{params.collection_name}': {e.message}"
            ) from e
