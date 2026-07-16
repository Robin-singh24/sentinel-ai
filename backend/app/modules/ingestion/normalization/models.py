"""Output model for the text normalization stage."""

from dataclasses import dataclass

from app.modules.ingestion.parsers.base import DocumentType


@dataclass(frozen=True)
class NormalizedDocument:
    """Normalized text produced by TextNormalizer, ready for chunking."""

    normalized_text: str
    original_filename: str
    document_type: DocumentType
    page_count: int
