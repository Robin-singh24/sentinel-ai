"""
Dependency injection for the vector store infrastructure.
"""

from fastapi import Request

from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.exceptions import SentinelVectorStoreError


def get_qdrant_manager(request: Request) -> QdrantConnectionManager:
    """
    Retrieves the QdrantConnectionManager from the application state.
    
    Returns:
        QdrantConnectionManager: The manager instance tied to the app lifecycle.
        
    Raises:
        SentinelVectorStoreError: If the manager is not found on app.state.
    """
    manager: QdrantConnectionManager | None = getattr(request.app.state, "qdrant_manager", None)
    if manager is None:
        raise SentinelVectorStoreError("QdrantConnectionManager is not initialized.")
    return manager
