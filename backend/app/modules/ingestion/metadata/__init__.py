"""Public API for the metadata generation sub-package."""

from app.modules.ingestion.metadata.generator import MetadataGenerator
from app.modules.ingestion.metadata.models import ProcessedChunk

__all__ = ["MetadataGenerator", "ProcessedChunk"]
