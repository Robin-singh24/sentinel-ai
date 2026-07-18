"""
Generic request and response models for Vector Repository operations.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict
from qdrant_client.models import Filter


class BaseRepositoryRequest(BaseModel):
    """Base class for all repository requests providing the target collection."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    collection_name: str


class VectorPoint(BaseModel):
    """Represents a single vector point."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    id: str | int
    vector: list[float]
    payload: dict[str, Any] | None = None


class UpsertRequest(BaseRepositoryRequest):
    """Request to upsert a single vector point."""
    point: VectorPoint


class UpsertBatchRequest(BaseRepositoryRequest):
    """Request to upsert multiple vector points."""
    points: list[VectorPoint]


class RetrieveRequest(BaseRepositoryRequest):
    """Request to retrieve a single vector by its ID."""
    vector_id: str | int


class RetrieveBatchRequest(BaseRepositoryRequest):
    """Request to retrieve multiple vectors by their IDs."""
    vector_ids: list[str | int]


class VectorSearchParams(BaseRepositoryRequest):
    """Parameters for executing a vector similarity search."""
    vector: list[float]
    limit: int = 5
    score_threshold: float | None = None
    filter: Filter | None = None


class VectorSearchResult(BaseModel):
    """Result of a vector similarity search."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    id: str | int
    score: float
    payload: dict[str, Any] | None = None
    vector: list[float] | None = None


class DeleteRequest(BaseRepositoryRequest):
    """Request to delete a single vector by its ID."""
    vector_id: str | int


class DeleteByFilterRequest(BaseRepositoryRequest):
    """Request to delete vectors matching a specific filter."""
    filter: Filter


class ScrollRequest(BaseRepositoryRequest):
    """Request to scroll through a collection."""
    limit: int = 10
    offset: str | int | None = None
    filter: Filter | None = None


class ScrollResult(BaseModel):
    """Result of a scroll operation."""
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    points: list[VectorPoint]
    next_page_offset: str | int | None = None


class CountRequest(BaseRepositoryRequest):
    """Request to count vectors in a collection."""
    filter: Filter | None = None
