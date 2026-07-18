"""
Integration and Regression tests for Vector Store infrastructure components.
"""

import pytest
from fastapi import FastAPI, Request

from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.manager import CollectionManager
from app.vectorstore.repositories.repository import VectorRepository
from app.vectorstore.dependencies import get_qdrant_manager, get_collection_manager, get_vector_repository


pytestmark = pytest.mark.asyncio


async def test_dependency_injection(qdrant_manager):
    """Validates the Dependency Injection chain for the entire Vector Store module."""
    app = FastAPI()
    app.state.qdrant_manager = qdrant_manager
    
    # Mocking FastAPI Request
    scope = {"type": "http", "app": app}
    request = Request(scope)
    
    # Test qdrant manager injection
    injected_qdrant = get_qdrant_manager(request)
    assert injected_qdrant is qdrant_manager
    
    # Test collection manager injection
    injected_collection = get_collection_manager(qdrant_manager=injected_qdrant)
    assert isinstance(injected_collection, CollectionManager)
    assert injected_collection._qdrant_manager is qdrant_manager
    
    # Test vector repository injection
    injected_repo = get_vector_repository(qdrant_manager=injected_qdrant)
    assert isinstance(injected_repo, VectorRepository)
    assert injected_repo._qdrant_manager is qdrant_manager
