"""Dependency injection factories for the Conversation Memory subsystem."""

from typing import Annotated

from app.config.settings import Settings, get_settings
from app.modules.conversations.dependencies import get_conversation_repository
from app.modules.conversations.repository import ConversationRepository
from app.modules.memory.formatter import MemoryFormatter
from app.modules.memory.service import ConversationMemoryService
from fastapi import Depends


def get_memory_service(
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> ConversationMemoryService:
    """Creates and returns an instance of ConversationMemoryService."""
    return ConversationMemoryService(repository=repository, settings=settings)


def get_memory_formatter() -> MemoryFormatter:
    """Creates and returns an instance of MemoryFormatter."""
    return MemoryFormatter()
