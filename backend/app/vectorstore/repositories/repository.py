"""
Generic Vector Repository.
"""

from qdrant_client.models import PointStruct

from app.core.logging import get_logger
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.exceptions import SentinelVectorStoreError
from app.vectorstore.repositories.models import (
    CountRequest,
    DeleteByFilterRequest,
    DeleteRequest,
    RetrieveBatchRequest,
    RetrieveRequest,
    ScrollRequest,
    ScrollResult,
    UpsertBatchRequest,
    UpsertRequest,
    VectorPoint,
    VectorSearchParams,
    VectorSearchResult,
)

logger = get_logger(__name__)


class VectorRepository:
    """
    Generic repository for Qdrant vector database operations.
    
    This class contains purely infrastructure-focused CRUD operations.
    It treats payloads as opaque dictionaries and does not enforce
    any business-specific logic.
    """

    def __init__(self, qdrant_manager: QdrantConnectionManager) -> None:
        self._qdrant_manager = qdrant_manager

    def _extract_vector(self, raw_vector: list[float] | dict[str, list[float]] | None) -> list[float]:
        """Extracts the default vector array if Qdrant returns a dictionary (named vectors)."""
        if isinstance(raw_vector, list):
            return raw_vector
        if isinstance(raw_vector, dict):
            return raw_vector.get("", [])
        return []

    async def upsert(self, request: UpsertRequest) -> None:
        """Upserts a single vector into the collection."""
        client = self._qdrant_manager.get_client()
        logger.info("Upserting vector.", extra={"collection": request.collection_name})
        try:
            await client.upsert(
                collection_name=request.collection_name,
                points=[
                    PointStruct(
                        id=request.point.id,
                        vector=request.point.vector,
                        payload=request.point.payload,
                    )
                ],
            )
        except Exception as e:
            logger.error("Failed to upsert vector.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to upsert vector in '{request.collection_name}': {e}") from e

    async def upsert_batch(self, request: UpsertBatchRequest) -> None:
        """Upserts a batch of vectors into the collection."""
        client = self._qdrant_manager.get_client()
        logger.info("Upserting batch of vectors.", extra={"collection": request.collection_name, "count": len(request.points)})
        try:
            points = [
                PointStruct(
                    id=p.id,
                    vector=p.vector,
                    payload=p.payload,
                )
                for p in request.points
            ]
            await client.upsert(
                collection_name=request.collection_name,
                points=points,
            )
        except Exception as e:
            logger.error("Failed to upsert vector batch.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to upsert batch in '{request.collection_name}': {e}") from e

    async def retrieve(self, request: RetrieveRequest) -> VectorPoint | None:
        """Retrieves a single vector by its ID."""
        client = self._qdrant_manager.get_client()
        try:
            records = await client.retrieve(
                collection_name=request.collection_name,
                ids=[request.vector_id],
                with_payload=True,
                with_vectors=True,
            )
            if not records:
                return None
            record = records[0]
            return VectorPoint(
                id=record.id,
                vector=self._extract_vector(record.vector),
                payload=record.payload,
            )
        except Exception as e:
            logger.error("Failed to retrieve vector.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to retrieve vector '{request.vector_id}': {e}") from e

    async def retrieve_batch(self, request: RetrieveBatchRequest) -> list[VectorPoint]:
        """Retrieves multiple vectors by their IDs."""
        client = self._qdrant_manager.get_client()
        try:
            records = await client.retrieve(
                collection_name=request.collection_name,
                ids=request.vector_ids,
                with_payload=True,
                with_vectors=True,
            )
            results = []
            for record in records:
                results.append(
                    VectorPoint(
                        id=record.id,
                        vector=self._extract_vector(record.vector),
                        payload=record.payload,
                    )
                )
            return results
        except Exception as e:
            logger.error("Failed to retrieve vector batch.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to retrieve batch in '{request.collection_name}': {e}") from e

    async def search(self, request: VectorSearchParams) -> list[VectorSearchResult]:
        """Executes a similarity search against the collection."""
        client = self._qdrant_manager.get_client()
        logger.info("Searching vectors.", extra={"collection": request.collection_name, "limit": request.limit})
        try:
            scored_points = await client.search(
                collection_name=request.collection_name,
                query_vector=request.vector,
                query_filter=request.filter,
                limit=request.limit,
                score_threshold=request.score_threshold,
                with_payload=True,
                with_vectors=True,
            )
            results = []
            for p in scored_points:
                results.append(
                    VectorSearchResult(
                        id=p.id,
                        score=p.score,
                        payload=p.payload,
                        vector=self._extract_vector(p.vector),
                    )
                )
            return results
        except Exception as e:
            logger.error("Failed to search vectors.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to search in '{request.collection_name}': {e}") from e

    async def delete(self, request: DeleteRequest) -> None:
        """Deletes a single vector by its ID."""
        client = self._qdrant_manager.get_client()
        logger.info("Deleting vector.", extra={"collection": request.collection_name})
        try:
            await client.delete(
                collection_name=request.collection_name,
                points_selector=[request.vector_id],
            )
        except Exception as e:
            logger.error("Failed to delete vector.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to delete vector '{request.vector_id}': {e}") from e

    async def delete_by_filter(self, request: DeleteByFilterRequest) -> None:
        """Deletes vectors matching the specified filter."""
        client = self._qdrant_manager.get_client()
        logger.info("Deleting vectors by filter.", extra={"collection": request.collection_name})
        try:
            await client.delete(
                collection_name=request.collection_name,
                points_selector=request.filter,
            )
        except Exception as e:
            logger.error("Failed to delete vectors by filter.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to delete by filter in '{request.collection_name}': {e}") from e

    async def scroll(self, request: ScrollRequest) -> ScrollResult:
        """Scrolls through the collection to retrieve vectors sequentially."""
        client = self._qdrant_manager.get_client()
        logger.info("Scrolling collection.", extra={"collection": request.collection_name, "limit": request.limit})
        try:
            records, next_page_offset = await client.scroll(
                collection_name=request.collection_name,
                scroll_filter=request.filter,
                limit=request.limit,
                offset=request.offset,
                with_payload=True,
                with_vectors=True,
            )
            points = []
            for record in records:
                points.append(
                    VectorPoint(
                        id=record.id,
                        vector=self._extract_vector(record.vector),
                        payload=record.payload,
                    )
                )
            return ScrollResult(points=points, next_page_offset=next_page_offset)
        except Exception as e:
            logger.error("Failed to scroll collection.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to scroll '{request.collection_name}': {e}") from e

    async def count(self, request: CountRequest) -> int:
        """Counts the total number of vectors, optionally matching a filter."""
        client = self._qdrant_manager.get_client()
        logger.info("Counting vectors.", extra={"collection": request.collection_name})
        try:
            count_result = await client.count(
                collection_name=request.collection_name,
                count_filter=request.filter,
                exact=True,
            )
            return count_result.count
        except Exception as e:
            logger.error("Failed to count vectors.", extra={"collection": request.collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to count '{request.collection_name}': {e}") from e
