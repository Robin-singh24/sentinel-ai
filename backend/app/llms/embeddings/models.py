"""Domain models for the embedding abstraction layer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingRequest:
    """Request payload containing text chunks for embedding."""
    texts: list[str]


@dataclass(frozen=True)
class EmbeddingResponse:
    """Standardized response from an embedding provider."""
    embeddings: list[list[float]]
    dimensions: int
    provider: str
    model: str
    processing_time_ms: float


from app.modules.ingestion.metadata.models import ProcessedChunk

@dataclass(frozen=True)
class EmbeddedChunk:
    """A processed chunk that has been enriched with its vector embedding."""
    chunk: ProcessedChunk
    vector: list[float]
    dimensions: int
