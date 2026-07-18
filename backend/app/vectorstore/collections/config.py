"""Configuration model for Qdrant collections."""

from pydantic import BaseModel, ConfigDict
from qdrant_client.models import Distance


class CollectionConfig(BaseModel):

    model_config = ConfigDict(frozen=True)

    name: str
    vector_size: int
    distance: Distance
