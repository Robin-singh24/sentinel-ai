"""Repository for managing Conversation persistence."""

import uuid

from app.common.exceptions import SentinelNotFoundError
from app.modules.conversations.models import Conversation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ConversationRepository:
    """Encapsulates SQLAlchemy database operations for the Conversation domain."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    async def get_conversation_with_messages(self, conversation_id: uuid.UUID) -> Conversation:
        """Retrieve a conversation along with its chronologically ordered messages."""
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        
        result = await self._session.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise SentinelNotFoundError(resource="conversation", identifier=str(conversation_id))
            
        return conversation
