"""
Qdrant connection manager.
"""

from typing import Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config.settings import Settings
from app.core.logging import get_logger
from app.vectorstore.exceptions import SentinelVectorStoreError

logger = get_logger(__name__)


class QdrantConnectionManager:
    """
    Manages the lifecycle of the AsyncQdrantClient.
    
    Responsibilities:
      - Lazy client initialization
      - Connection health validation
      - Graceful shutdown
      
    This manager does NOT contain business logic for collections, vectors, or search.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Optional[AsyncQdrantClient] = None

    def is_initialized(self) -> bool:
        """Returns True if the underlying client has been instantiated."""
        return self._client is not None

    def get_client(self) -> AsyncQdrantClient:
        """
        Lazily initializes and returns the AsyncQdrantClient.
        
        Returns:
            AsyncQdrantClient: The underlying Qdrant client.
        """
        if self._client is None:
            logger.info(
                "Initializing Qdrant client.",
                extra={
                    "qdrant_url": self._settings.qdrant_url,
                    "qdrant_timeout": self._settings.qdrant_timeout,
                }
            )
            self._client = AsyncQdrantClient(
                url=self._settings.qdrant_url,
                api_key=self._settings.qdrant_api_key,
                timeout=self._settings.qdrant_timeout,
            )
        return self._client

    async def check_health(self) -> bool:
        """
        Validates the connection to Qdrant using a lightweight operation.
        
        Returns:
            bool: True if connection is successful.
            
        Raises:
            SentinelVectorStoreError: If the health check fails or times out.
        """
        client = self.get_client()
        try:
            logger.info("Starting Qdrant health check.")
            # Using get_collections() as a lightweight operation to verify connectivity
            await client.get_collections()
            logger.info("Qdrant health check succeeded.")
            return True
        except UnexpectedResponse as e:
            logger.error("Qdrant health check failed due to unexpected response.", extra={"error": str(e)})
            raise SentinelVectorStoreError(f"Qdrant returned an unexpected response: {e}") from e
        except Exception as e:
            logger.error("Qdrant health check failed.", extra={"error": str(e)})
            raise SentinelVectorStoreError(f"Failed to connect to Qdrant: {e}") from e

    async def close(self) -> None:
        """Closes the client gracefully if initialized."""
        if self._client is not None:
            logger.info("Shutting down Qdrant client.")
            await self._client.close()
            self._client = None
            logger.info("Qdrant client shut down successfully.")
