"""Service orchestrating Conversation Memory operations."""

import asyncio
import uuid

from app.common.exceptions import SentinelNotFoundError
from app.config.settings import Settings
from app.core.logging import get_logger
from app.modules.conversations.repository import ConversationRepository
from app.modules.memory.exceptions import SentinelMemoryError
from app.modules.memory.models import ConversationMemory, MemoryMessage, MemoryRole
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)


class ConversationMemoryService:
    """Manages the retrieval and assembly of conversation memory."""

    def __init__(self, repository: ConversationRepository, settings: Settings) -> None:
        """Initialize the service with a ConversationRepository and Settings."""
        self._repository = repository
        self._settings = settings

    def _apply_window(self, messages: list[MemoryMessage]) -> list[MemoryMessage]:
        """Apply the configured memory window policy to a list of messages."""
        window_size = self._settings.memory_window_size
        if window_size <= 0:
            return []
        
        # Python list slicing safely handles if len(messages) < window_size
        return messages[-window_size:]

    async def get_memory(self, conversation_id: uuid.UUID) -> ConversationMemory:
        """Retrieves conversation memory for the specified conversation."""
        logger.debug(
            "Retrieving memory for conversation.",
            extra={"conversation_id": str(conversation_id)}
        )
        
        try:
            conversation = await self._repository.get_by_id(conversation_id, include_messages=True)
        except SentinelNotFoundError:
            # Let the 404 pass through unchanged
            raise
        except asyncio.CancelledError:
            logger.warning("Memory retrieval cancelled by user/system.")
            raise
        except SQLAlchemyError as e:
            logger.error("Database error retrieving memory.", exc_info=True)
            raise SentinelMemoryError(
                "Failed to retrieve conversation memory from the database."
            ) from e
        except Exception as e:
            logger.error("Unexpected error retrieving memory.", exc_info=True)
            raise SentinelMemoryError("An unexpected error occurred retrieving memory.") from e

        sorted_messages = sorted(conversation.messages, key=lambda m: m.created_at)

        memory_messages = [
            MemoryMessage(
                role=MemoryRole(msg.role.value),
                content=msg.content
            )
            for msg in sorted_messages
        ]
        
        windowed_messages = self._apply_window(memory_messages)

        return ConversationMemory(messages=windowed_messages)
