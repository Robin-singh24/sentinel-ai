"""
Integration tests for Phase 8.2: Qdrant Collection Management.
"""

import logging
import uuid
import pytest
from qdrant_client.models import Distance

from app.config.settings import get_settings, Settings
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.config import CollectionConfig
from app.vectorstore.collections.manager import CollectionManager
from app.vectorstore.exceptions import SentinelVectorStoreError


pytestmark = pytest.mark.asyncio





async def test_collection_creation_and_existence(collection_manager, test_collection_config, caplog):
    """Validates collection creation (1), existence (2), and structured logging (8)."""
    assert not await collection_manager.collection_exists(test_collection_config.name)
    
    with caplog.at_level(logging.INFO):
        await collection_manager.create_collection(test_collection_config)
    
    assert "Creating collection." in caplog.text
    assert "Collection created successfully." in caplog.text
    
    assert await collection_manager.collection_exists(test_collection_config.name)


async def test_collection_metadata(collection_manager, test_collection_config):
    """Validates collection metadata retrieval (3)."""
    await collection_manager.create_collection(test_collection_config)
    
    info = await collection_manager.get_collection(test_collection_config.name)
    assert info.status.name == "GREEN"
    assert info.config.params.vectors.size == test_collection_config.vector_size
    assert info.config.params.vectors.distance == test_collection_config.distance


async def test_idempotent_ensure_collection(collection_manager, test_collection_config, caplog):
    """Validates idempotent ensure_collection() behavior (4)."""
    # First call: Should create it
    await collection_manager.ensure_collection(test_collection_config)
    assert await collection_manager.collection_exists(test_collection_config.name)
    
    caplog.clear()
    
    # Second call: Should return early
    with caplog.at_level(logging.INFO):
        await collection_manager.ensure_collection(test_collection_config)
    
    assert "Collection already exists." in caplog.text
    assert "Creating collection." not in caplog.text


async def test_delete_collection(collection_manager, test_collection_config, caplog):
    """Validates collection deletion (5)."""
    await collection_manager.create_collection(test_collection_config)
    assert await collection_manager.collection_exists(test_collection_config.name)
    
    with caplog.at_level(logging.INFO):
        await collection_manager.delete_collection(test_collection_config.name)
        
    assert "Deleting collection." in caplog.text
    assert "Collection deleted successfully." in caplog.text
    
    assert not await collection_manager.collection_exists(test_collection_config.name)


async def test_recreate_collection(collection_manager, test_collection_config):
    """Validates explicit collection recreation (6)."""
    await collection_manager.create_collection(test_collection_config)
    info1 = await collection_manager.get_collection(test_collection_config.name)
    
    await collection_manager.recreate_collection(test_collection_config)
    info2 = await collection_manager.get_collection(test_collection_config.name)
    
    assert info2.config.params.vectors.size == test_collection_config.vector_size
    assert info1 is not info2


async def test_exception_handling():
    """Validates exception encapsulation and chaining when Qdrant is unavailable (7)."""
    bad_settings = Settings(qdrant_port=9999) # Intentionally wrong port
    bad_manager = QdrantConnectionManager(bad_settings)
    col_mgr = CollectionManager(bad_manager)
    
    config = CollectionConfig(name="will_fail", vector_size=128, distance=Distance.COSINE)
    
    with pytest.raises(SentinelVectorStoreError) as exc_info:
        await col_mgr.collection_exists(config.name)
        
    assert "Failed to check existence for collection" in str(exc_info.value)
    
    await bad_manager.close()
