"""Output models for the metadata generation stage."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ProcessedChunk:
    """A semantic text chunk enriched with downstream metadata."""

    chunk_id: str
    document_id: UUID
    workspace_id: UUID
    chunk_index: int
    content: str
    character_count: int
    token_count: int
    page_number: int | None
