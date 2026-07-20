"""Dependency injection factories for the Conversations subsystem."""

from typing import Annotated

from app.database.dependency import get_db_session
from app.modules.conversations.repository import ConversationRepository
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_conversation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationRepository:
    """Creates and returns an instance of ConversationRepository."""
    return ConversationRepository(session=session)
