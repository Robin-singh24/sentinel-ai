"""Output models for the chunking engine."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """A semantic text segment produced by the Chunking Engine."""

    chunk_index: int
    content: str
    character_count: int
