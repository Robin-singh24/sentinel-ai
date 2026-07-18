"""
Shared fixtures for Vector Store integration tests.
"""

import uuid
import pytest
from qdrant_client.models import Distance

from app.config.settings import get_settings
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.config import CollectionConfig
from app.vectorstore.collections.manager import CollectionManager
from app.vectorstore.repositories.repository import VectorRepository


@pytest.fixture
async def qdrant_manager():
    """Provides a real QdrantConnectionManager connected to the Docker environment."""
    settings = get_settings()
    manager = QdrantConnectionManager(settings)
    yield manager
    await manager.close()


@pytest.fixture
async def collection_manager(qdrant_manager):
    """Provides the CollectionManager under test."""
    return CollectionManager(qdrant_manager)


@pytest.fixture
async def vector_repository(qdrant_manager):
    """Provides the VectorRepository under test."""
    return VectorRepository(qdrant_manager)


@pytest.fixture
async def test_collection_config(collection_manager):
    """Provides a deterministic collection configuration and ensures cleanup."""
    name = f"test_col_{uuid.uuid4().hex[:8]}"
    config = CollectionConfig(
        name=name,
        vector_size=384,
        distance=Distance.COSINE
    )
    yield config
    
    try:
        await collection_manager.delete_collection(name)
    except Exception:
        pass


@pytest.fixture
async def test_collection(collection_manager):
    """Provides a deterministic collection specifically for repository testing with Distance.DOT."""
    name = f"test_repo_{uuid.uuid4().hex[:8]}"
    config = CollectionConfig(
        name=name,
        vector_size=2, # Small vectors for ease of testing
        distance=Distance.DOT
    )
    
    await collection_manager.create_collection(config)
    yield name
    
    try:
        await collection_manager.delete_collection(name)
    except Exception:
        pass
