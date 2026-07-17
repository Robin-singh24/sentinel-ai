"""Domain models for the ingestion module."""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True)
class DocumentProcessingContext:
    """Provides necessary context to the processing orchestrator."""

    document_id: UUID
    workspace_id: UUID
    file_path: Path
    original_filename: str
    mime_type: str
