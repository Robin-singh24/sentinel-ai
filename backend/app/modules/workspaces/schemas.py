"""Workspace request and response DTOs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkspaceCreate(BaseModel):
    """Request body for creating a new workspace."""

    name: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Strip leading/trailing whitespace before length constraints are applied."""
        if isinstance(value, str):
            return value.strip()
        return value


class WorkspaceUpdate(BaseModel):
    """Request body for updating an existing workspace (all fields optional)."""

    name: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        """Strip leading/trailing whitespace before length constraints are applied."""
        if isinstance(value, str):
            return value.strip()
        return value


class WorkspaceResponse(BaseModel):
    """Response DTO for workspace data — owner_id is never exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
