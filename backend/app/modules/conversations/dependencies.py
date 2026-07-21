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


from app.agents.response.dependencies import get_response_service
from app.agents.response.service import ResponseService
from app.agents.supervisor.dependencies import get_supervisor_service
from app.agents.supervisor.service import SupervisorService
from app.modules.conversations.service import ConversationService
from app.modules.workspaces.repository import WorkspaceRepository


def get_conversation_service(
    conversation_repo: Annotated[ConversationRepository, Depends(get_conversation_repository)],
    supervisor_service: Annotated[SupervisorService, Depends(get_supervisor_service)],
    response_service: Annotated[ResponseService, Depends(get_response_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationService:
    """Creates and returns an instance of ConversationService."""
    workspace_repo = WorkspaceRepository(session=session)
    return ConversationService(
        conversation_repo=conversation_repo,
        workspace_repo=workspace_repo,
        supervisor_service=supervisor_service,
        response_service=response_service,
        session=session,
    )
