"""
Integration tests for Phase 8.3: Vector Repository.
"""

import uuid
import pytest
from qdrant_client.models import Distance, Filter, FieldCondition, MatchValue

from app.config.settings import get_settings
from app.vectorstore.client.qdrant import QdrantConnectionManager
from app.vectorstore.collections.config import CollectionConfig
from app.vectorstore.collections.manager import CollectionManager
from app.vectorstore.repositories.repository import VectorRepository
from app.vectorstore.repositories.models import (
    UpsertRequest, UpsertBatchRequest, RetrieveRequest, RetrieveBatchRequest,
    VectorSearchParams, DeleteRequest, DeleteByFilterRequest, ScrollRequest,
    CountRequest, VectorPoint
)


pytestmark = pytest.mark.asyncio





async def test_upsert_and_retrieve(vector_repository, test_collection):
    """Validates single vector upsert and retrieval."""
    uid1 = str(uuid.uuid4())
    point = VectorPoint(id=uid1, vector=[0.1, 0.9], payload={"category": "test"})
    
    req_up = UpsertRequest(collection_name=test_collection, point=point)
    await vector_repository.upsert(req_up)
    
    req_ret = RetrieveRequest(collection_name=test_collection, vector_id=uid1)
    retrieved = await vector_repository.retrieve(req_ret)
    
    assert retrieved is not None
    assert retrieved.id == uid1
    assert retrieved.vector == [0.1, 0.9]
    assert retrieved.payload == {"category": "test"}


async def test_batch_upsert_and_retrieve(vector_repository, test_collection):
    """Validates batch upsert and retrieval."""
    uid1, uid2 = str(uuid.uuid4()), str(uuid.uuid4())
    points = [
        VectorPoint(id=uid1, vector=[1.0, 0.0], payload={"type": "A"}),
        VectorPoint(id=uid2, vector=[0.0, 1.0], payload={"type": "B"})
    ]
    
    req_up = UpsertBatchRequest(collection_name=test_collection, points=points)
    await vector_repository.upsert_batch(req_up)
    
    req_ret = RetrieveBatchRequest(collection_name=test_collection, vector_ids=[uid1, uid2, str(uuid.uuid4())])
    retrieved = await vector_repository.retrieve_batch(req_ret)
    
    assert len(retrieved) == 2
    ids = [p.id for p in retrieved]
    assert uid1 in ids
    assert uid2 in ids


async def test_search_and_count(vector_repository, test_collection):
    """Validates search functionality and counting."""
    uid1 = str(uuid.uuid4())
    points = [
        VectorPoint(id=uid1, vector=[1.0, 0.0], payload={"group": "first"}),
        VectorPoint(id=str(uuid.uuid4()), vector=[0.9, 0.1], payload={"group": "first"}),
        VectorPoint(id=str(uuid.uuid4()), vector=[0.0, 1.0], payload={"group": "second"})
    ]
    await vector_repository.upsert_batch(UpsertBatchRequest(collection_name=test_collection, points=points))
    
    # Wait briefly or rely on immediate consistency? Qdrant is typically quite fast for small data, but wait if needed.
    # We will assume it's synchronous enough for this tiny set.
    
    # Test count
    count = await vector_repository.count(CountRequest(collection_name=test_collection))
    assert count == 3
    
    count_first = await vector_repository.count(
        CountRequest(
            collection_name=test_collection, 
            filter=Filter(must=[FieldCondition(key="group", match=MatchValue(value="first"))])
        )
    )
    assert count_first == 2

    # Test search
    search_req = VectorSearchParams(
        collection_name=test_collection,
        vector=[1.0, 0.0],
        limit=2
    )
    results = await vector_repository.search(search_req)
    assert len(results) == 2
    assert results[0].id == uid1 # Closest


async def test_delete_and_delete_by_filter(vector_repository, test_collection):
    """Validates single deletion and bulk deletion by filter."""
    uid1, uid2 = str(uuid.uuid4()), str(uuid.uuid4())
    points = [
        VectorPoint(id=uid1, vector=[0.5, 0.5], payload={"status": "active"}),
        VectorPoint(id=uid2, vector=[0.6, 0.4], payload={"status": "archived"})
    ]
    await vector_repository.upsert_batch(UpsertBatchRequest(collection_name=test_collection, points=points))
    
    # Delete single
    await vector_repository.delete(DeleteRequest(collection_name=test_collection, vector_id=uid1))
    
    ret_d1 = await vector_repository.retrieve(RetrieveRequest(collection_name=test_collection, vector_id=uid1))
    assert ret_d1 is None
    
    # Delete by filter
    filter_obj = Filter(must=[FieldCondition(key="status", match=MatchValue(value="archived"))])
    await vector_repository.delete_by_filter(DeleteByFilterRequest(collection_name=test_collection, filter=filter_obj))
    
    ret_d2 = await vector_repository.retrieve(RetrieveRequest(collection_name=test_collection, vector_id=uid2))
    assert ret_d2 is None


async def test_scroll(vector_repository, test_collection):
    """Validates scrolling through the collection."""
    points = [VectorPoint(id=str(uuid.uuid4()), vector=[0.5, 0.5], payload={"seq": i}) for i in range(5)]
    await vector_repository.upsert_batch(UpsertBatchRequest(collection_name=test_collection, points=points))
    
    scroll_req = ScrollRequest(collection_name=test_collection, limit=3)
    res1 = await vector_repository.scroll(scroll_req)
    
    assert len(res1.points) == 3
    assert res1.next_page_offset is not None
    
    scroll_req2 = ScrollRequest(collection_name=test_collection, limit=3, offset=res1.next_page_offset)
    res2 = await vector_repository.scroll(scroll_req2)
    
    assert len(res2.points) == 2
    assert res2.next_page_offset is None