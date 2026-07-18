"""
Collection lifecycle manager.
"""

from qdrant_client.models import CollectionInfo, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.logging import get_logger
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.config import CollectionConfig
from app.vectorstore.exceptions import SentinelVectorStoreError

logger = get_logger(__name__)


class CollectionManager:
    """Manages Qdrant collection lifecycle operations."""

    def __init__(self, qdrant_manager: QdrantConnectionManager) -> None:
        self._qdrant_manager = qdrant_manager

    async def collection_exists(self, collection_name: str) -> bool:
        """Checks whether the collection exists on the Qdrant server."""
        client = self._qdrant_manager.get_client()
        try:
            return await client.collection_exists(collection_name)
        except Exception as e:
            logger.error("Failed to check collection existence.", extra={"collection": collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to check existence for collection '{collection_name}': {e}") from e

    async def get_collection(self, collection_name: str) -> CollectionInfo:
        """Retrieves collection metadata."""
        client = self._qdrant_manager.get_client()
        try:
            return await client.get_collection(collection_name)
        except UnexpectedResponse as e:
            if e.status_code == 404:
                raise SentinelVectorStoreError(f"Collection '{collection_name}' not found.") from e
            logger.error("Failed to retrieve collection info.", extra={"collection": collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to get collection '{collection_name}': {e}") from e
        except Exception as e:
            logger.error("Failed to retrieve collection info.", extra={"collection": collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to get collection '{collection_name}': {e}") from e

    async def create_collection(self, config: CollectionConfig) -> None:
        """Creates a collection based on the given configuration."""
        client = self._qdrant_manager.get_client()
        logger.info("Creating collection.", extra={"collection": config.name})
        try:
            await client.create_collection(
                collection_name=config.name,
                vectors_config=VectorParams(
                    size=config.vector_size,
                    distance=config.distance
                )
            )
            logger.info("Collection created successfully.", extra={"collection": config.name})
        except Exception as e:
            logger.error("Failed to create collection.", extra={"collection": config.name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to create collection '{config.name}': {e}") from e

    async def ensure_collection(self, config: CollectionConfig) -> None:
        """Idempotently ensures the collection exists."""

        if await self.collection_exists(config.name):
            logger.info("Collection already exists.", extra={"collection": config.name})
            return
        await self.create_collection(config)

    async def delete_collection(self, collection_name: str) -> None:
        """Deletes the collection. Gracefully ignores 404s."""
        
        client = self._qdrant_manager.get_client()
        logger.info("Deleting collection.", extra={"collection": collection_name})
        try:
            await client.delete_collection(collection_name)
            logger.info("Collection deleted successfully.", extra={"collection": collection_name})
        except UnexpectedResponse as e:
            if e.status_code == 404:
                logger.info("Collection not found for deletion.", extra={"collection": collection_name})
                return
            logger.error("Failed to delete collection.", extra={"collection": collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to delete collection '{collection_name}': {e}") from e
        except Exception as e:
            logger.error("Failed to delete collection.", extra={"collection": collection_name, "error": str(e)})
            raise SentinelVectorStoreError(f"Failed to delete collection '{collection_name}': {e}") from e

    async def recreate_collection(self, config: CollectionConfig) -> None:
        """Explicitly deletes the collection if it exists and creates a new one."""
        await self.delete_collection(config.name)
        await self.create_collection(config)
