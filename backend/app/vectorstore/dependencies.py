"""
Dependency injection for the vector store infrastructure.
"""

from fastapi import Request, Depends

from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.manager import CollectionManager
from app.vectorstore.exceptions import SentinelVectorStoreError


def get_qdrant_manager(request: Request) -> QdrantConnectionManager:
    """Retrieves the QdrantConnectionManager from the application state."""
    manager: QdrantConnectionManager | None = getattr(request.app.state, "qdrant_manager", None)
    if manager is None:
        raise SentinelVectorStoreError("QdrantConnectionManager is not initialized.")
    return manager


def get_collection_manager(
    qdrant_manager: QdrantConnectionManager = Depends(get_qdrant_manager),
) -> CollectionManager:
    """Retrieves the CollectionManager initialized with the application's QdrantConnectionManager."""
    return CollectionManager(qdrant_manager=qdrant_manager)
