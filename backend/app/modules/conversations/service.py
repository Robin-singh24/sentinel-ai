"""Conversation service — business logic and transaction management."""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.response.service import ResponseService
from app.agents.supervisor.service import SupervisorService
from app.common.exceptions import SentinelNotFoundError
from app.modules.conversations.models import Conversation, Message, MessageRole
from app.modules.conversations.repository import ConversationRepository
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.repository import WorkspaceRepository


class ConversationService:
    """Orchestrates conversations, messages, and AI workflows."""

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        workspace_repo: WorkspaceRepository,
        supervisor_service: SupervisorService,
        response_service: ResponseService,
        session: AsyncSession,
    ) -> None:
        """Initialize the ConversationService."""
        self._conversation_repo = conversation_repo
        self._workspace_repo = workspace_repo
        self._supervisor_service = supervisor_service
        self._response_service = response_service
        self._session = session

    async def create_conversation(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
        title: str | None = None,
    ) -> Conversation:
        """Create a new conversation."""
        await self._get_workspace(workspace_id, owner_id)

        conversation = Conversation(
            workspace_id=workspace_id,
            user_id=owner_id,
            title=title,
        )
        
        try:
            conversation = await self._conversation_repo.create(conversation)
            await self._session.commit()
            return await self._get_owned_conversation(conversation.id, owner_id)
        except Exception:
            await self._session.rollback()
            raise

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Conversation:
        """Retrieve an owned conversation by ID."""
        return await self._get_owned_conversation(conversation_id, owner_id)

    async def list_conversations(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Sequence[Conversation]:
        """List all conversations for a specific workspace and user."""
        await self._get_workspace(workspace_id, owner_id)
        return await self._conversation_repo.list_by_workspace(workspace_id, owner_id)

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> None:
        """Delete an owned conversation."""
        conversation = await self._get_owned_conversation(conversation_id, owner_id)
        try:
            await self._conversation_repo.delete(conversation)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def send_message(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
        content: str,
    ) -> Message:
        """Process a user message and generate an assistant response atomically."""
        try:
            # The transaction wraps the entire execution
            assistant_message = await self._execute_chat_workflow(
                conversation_id=conversation_id,
                owner_id=owner_id,
                content=content,
            )
            await self._session.commit()
            return assistant_message
        except Exception:
            await self._session.rollback()
            raise

    async def _execute_chat_workflow(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
        content: str,
    ) -> Message:
        """Execute the orchestration workflow without transaction concerns."""
        conversation = await self._get_owned_conversation(conversation_id, owner_id)

        # 1. Persist user message
        user_message = await self._persist_user_message(conversation.id, content)

        assistant_message = await self._generate_assistant_response(conversation.id, content)
        
        # 4. Persist assistant message
        return await self._persist_assistant_message(assistant_message)

    async def _persist_user_message(self, conversation_id: uuid.UUID, content: str) -> Message:
        """Create and flush the user message."""
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.user,
            content=content,
        )
        return await self._conversation_repo.create_message(user_message)

    async def _generate_assistant_response(self, conversation_id: uuid.UUID, content: str) -> Message:
        """Coordinate with the AI layers to generate a response."""
        # Supervisor processes the query and plans/executes workflow (e.g. retrieval)
        workflow_result = await self._supervisor_service.process_query(content)
        
        # Response service coordinates memory retrieval, context formatting, and LLM invocation
        generated = await self._response_service.generate_response(
            query=content,
            workflow_result=workflow_result,
            conversation_id=conversation_id,
        )
        
        return Message(
            conversation_id=conversation_id,
            role=MessageRole.assistant,
            content=generated.content,
        )

    async def _persist_assistant_message(self, message: Message) -> Message:
        """Persist and flush the assistant message."""
        return await self._conversation_repo.create_message(message)

    async def _get_workspace(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Workspace:
        """Ensure the workspace exists and belongs to the owner."""
        workspace = await self._workspace_repo.get_by_id(workspace_id, owner_id)
        if workspace is None:
            raise SentinelNotFoundError(resource="Workspace", identifier=str(workspace_id))
        return workspace

    async def _get_owned_conversation(
        self,
        conversation_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Conversation:
        """Load conversation and ensure ownership."""
        conversation = await self._conversation_repo.get_by_id(conversation_id, include_messages=True)
        if conversation is None or conversation.user_id != owner_id:
            raise SentinelNotFoundError(resource="Conversation", identifier=str(conversation_id))
        return conversation
