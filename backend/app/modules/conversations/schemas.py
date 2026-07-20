"""Conversation request and response DTOs."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from app.modules.conversations.models import MessageRole


class MessageResponse(BaseModel):
    """Response DTO for a single chat message."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    citations: list | None = None
    created_at: datetime


class ConversationSummaryResponse(BaseModel):
    """Lightweight response DTO for a conversation in list views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class ConversationResponse(BaseModel):
    """Response DTO for a complete conversation, including messages."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]


class CreateConversationRequest(BaseModel):
    """Payload for creating a new conversation."""

    title: str | None = Field(default=None, max_length=500)


class SendMessageRequest(BaseModel):
    """Payload for sending a user message to a conversation."""

    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SendMessageResponse(BaseModel):
    """Response returned after sending a message."""
    assistant: MessageResponse
