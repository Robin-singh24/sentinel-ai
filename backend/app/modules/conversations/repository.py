"""Repository for managing Conversation persistence."""

import uuid
from typing import Sequence

from app.common.exceptions import SentinelNotFoundError
from app.modules.conversations.models import Conversation, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ConversationRepository:
    """Encapsulates SQLAlchemy database operations for the Conversation domain."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, conversation: Conversation) -> Conversation:
        """Persist a new Conversation entity.
        
        Flushes the session so database-generated values (IDs, timestamps)
        are available to the Service before the transaction is committed.
        """
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def get_by_id(self, conversation_id: uuid.UUID, include_messages: bool = False) -> Conversation:
        """Retrieve a conversation by ID."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        
        if include_messages:
            stmt = stmt.options(selectinload(Conversation.messages))
            
        result = await self._session.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise SentinelNotFoundError(resource="conversation", identifier=str(conversation_id))
            
        return conversation

    async def list_by_workspace(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> Sequence[Conversation]:
        """Return all conversations belonging to a specific workspace and user."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.user_id == user_id
            )
            .order_by(Conversation.updated_at.desc())
        )
        
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def delete(self, conversation: Conversation) -> None:
        """Delete an existing Conversation."""
        await self._session.delete(conversation)

    async def create_message(self, message: Message) -> Message:
        """Persist a new Message entity."""
        self._session.add(message)
        await self._session.flush()
        return message

    async def list_messages(self, conversation_id: uuid.UUID) -> Sequence[Message]:
        """Return all messages for a specific conversation."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        
        result = await self._session.execute(stmt)
        return result.scalars().all()
