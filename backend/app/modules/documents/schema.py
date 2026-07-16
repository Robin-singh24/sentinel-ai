"""Document request and response DTOs."""

import uuid
from datetime import datetime

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict

# Re-export so callers import DocumentStatus from the schema layer, not the model layer
from app.modules.documents.models import DocumentStatus


class DocumentUpload(BaseModel):
    """Form-data schema for a single document upload.

    workspace_id is supplied as a path parameter; this schema carries only the
    file itself so FastAPI can bind it from multipart/form-data.
    """

    file: UploadFile


class DocumentResponse(BaseModel):
    """Response DTO for document data.

    Intentionally omits checksum, storage_path, and uploaded_by to avoid
    exposing internal storage details and ownership identifiers to clients.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    status: DocumentStatus
    uploaded_at: datetime
