"""
Regression tests for Vector Store search edge cases.
"""

import uuid
import pytest
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.vectorstore.repositories.models import (
    VectorSearchParams, VectorPoint, UpsertRequest, RetrieveRequest
)
from app.vectorstore.exceptions import SentinelVectorStoreError


pytestmark = pytest.mark.asyncio


async def test_empty_search_results(vector_repository, test_collection):
    """Validates that search correctly handles queries matching no records."""
    search_req = VectorSearchParams(
        collection_name=test_collection,
        vector=[1.0, 1.0],
        limit=5,
        filter=Filter(must=[FieldCondition(key="nonexistent_key", match=MatchValue(value="impossible"))])
    )
    
    results = await vector_repository.search(search_req)
    assert len(results) == 0


async def test_invalid_collection_search(vector_repository):
    """Validates that querying a non-existent collection correctly raises wrapped SentinelVectorStoreError."""
    search_req = VectorSearchParams(
        collection_name="this_collection_does_not_exist",
        vector=[1.0, 0.0],
        limit=5
    )
    
    with pytest.raises(SentinelVectorStoreError) as exc_info:
        await vector_repository.search(search_req)
        
    assert "Failed to search in 'this_collection_does_not_exist'" in str(exc_info.value)


async def test_invalid_vector_dimensions(vector_repository, test_collection):
    """Validates that upserting vectors with incorrect dimensions raises wrapped SentinelVectorStoreError."""
    # test_collection expects dimension 2
    uid = str(uuid.uuid4())
    point = VectorPoint(id=uid, vector=[1.0, 0.5, 0.2]) # Dimension 3
    
    req_up = UpsertRequest(collection_name=test_collection, point=point)
    with pytest.raises(SentinelVectorStoreError) as exc_info:
        await vector_repository.upsert(req_up)
        
    assert "Failed to upsert vector in" in str(exc_info.value)


async def test_vector_overwrite_semantics(vector_repository, test_collection):
    """Validates that upserting an existing ID successfully overwrites its vector and payload."""
    uid = str(uuid.uuid4())
    point1 = VectorPoint(id=uid, vector=[1.0, 0.0], payload={"status": "initial"})
    
    await vector_repository.upsert(UpsertRequest(collection_name=test_collection, point=point1))
    
    point2 = VectorPoint(id=uid, vector=[0.0, 1.0], payload={"status": "overwritten"})
    
    await vector_repository.upsert(UpsertRequest(collection_name=test_collection, point=point2))
    
    retrieved = await vector_repository.retrieve(RetrieveRequest(collection_name=test_collection, vector_id=uid))
    
    assert retrieved is not None
    assert retrieved.payload == {"status": "overwritten"}
    assert retrieved.vector == [0.0, 1.0]


async def test_retrieve_nonexistent_vector(vector_repository, test_collection):
    """Validates that retrieving a missing vector ID returns None safely."""
    missing_uid = str(uuid.uuid4())
    req_ret = RetrieveRequest(collection_name=test_collection, vector_id=missing_uid)
    retrieved = await vector_repository.retrieve(req_ret)
    assert retrieved is None
