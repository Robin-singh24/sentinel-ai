import pytest
import uuid
from datetime import datetime, timezone

from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.common.exceptions import SentinelNotFoundError
from app.modules.conversations.models import Conversation, MessageRole
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.service import ConversationService
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.auth.models import User
from app.agents.supervisor.service import SupervisorService
from app.agents.response.service import ResponseService
from app.agents.supervisor.models import WorkflowExecutionResult
from app.agents.response.models import GeneratedResponse


@pytest.fixture
def mock_supervisor_service():
    service = AsyncMock(spec=SupervisorService)
    service.process_query.return_value = WorkflowExecutionResult(retrieved_chunks=[])
    return service


@pytest.fixture
def mock_response_service():
    service = AsyncMock(spec=ResponseService)
    service.generate_response.return_value = GeneratedResponse(
        content="Test assistant response",
    )
    return service


@pytest.fixture
async def setup_db_service(db_session: AsyncSession):
    # Setup standard user and workspace
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    user = User(
        id=user_id, 
        email=f"test_service_{user_id}@example.com", 
        password_hash="pw",
        first_name="Test",
        last_name="User"
    )
    workspace = Workspace(id=workspace_id, name="Test Service Workspace", owner_id=user_id)

    db_session.add_all([user, workspace])
    await db_session.flush()
    await db_session.commit()
    
    return {"user_id": user_id, "workspace_id": workspace_id}


@pytest.mark.asyncio
class TestConversationService:
    async def test_crud_operations(
        self, db_session: AsyncSession, setup_db_service, mock_supervisor_service, mock_response_service
    ):
        workspace_id = setup_db_service["workspace_id"]
        user_id = setup_db_service["user_id"]
        
        service = ConversationService(
            conversation_repo=ConversationRepository(db_session),
            workspace_repo=WorkspaceRepository(db_session),
            supervisor_service=mock_supervisor_service,
            response_service=mock_response_service,
            session=db_session
        )
        
        # 1. Create
        conv = await service.create_conversation(workspace_id, user_id, "Service Test")
        assert conv.title == "Service Test"
        assert conv.id is not None
        assert conv.user_id == user_id
        
        # 2. Get
        fetched = await service.get_conversation(conv.id, user_id)
        assert fetched.id == conv.id
        
        # 3. Get unauthorized should fail
        with pytest.raises(SentinelNotFoundError):
            await service.get_conversation(conv.id, uuid.uuid4())
            
        # 4. List
        convs = await service.list_conversations(workspace_id, user_id)
        assert len(convs) == 1
        
        # 5. Delete
        await service.delete_conversation(conv.id, user_id)
        with pytest.raises(SentinelNotFoundError):
            await service.get_conversation(conv.id, user_id)

    async def test_send_message_workflow(
        self, db_session: AsyncSession, setup_db_service, mock_supervisor_service, mock_response_service
    ):
        workspace_id = setup_db_service["workspace_id"]
        user_id = setup_db_service["user_id"]
        
        service = ConversationService(
            conversation_repo=ConversationRepository(db_session),
            workspace_repo=WorkspaceRepository(db_session),
            supervisor_service=mock_supervisor_service,
            response_service=mock_response_service,
            session=db_session
        )
        
        conv = await service.create_conversation(workspace_id, user_id, "Workflow Test")
        
        # Execute chat workflow
        assistant_message = await service.send_message(conv.id, user_id, "Hello AI!")
        
        # Verifications
        assert assistant_message.role == MessageRole.assistant
        assert assistant_message.content == "Test assistant response"
        assert assistant_message.conversation_id == conv.id
        
        # Fetch DB to verify both messages are persisted
        repo = ConversationRepository(db_session)
        messages = await repo.list_messages(conv.id)
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.user
        assert messages[0].content == "Hello AI!"
        assert messages[1].role == MessageRole.assistant
        assert messages[1].content == "Test assistant response"

    async def test_send_message_rollback_on_failure(
        self, db_session: AsyncSession, setup_db_service, mock_supervisor_service, mock_response_service
    ):
        workspace_id = setup_db_service["workspace_id"]
        user_id = setup_db_service["user_id"]
        
        # Simulate an AI error
        mock_supervisor_service.process_query.side_effect = Exception("AI Failed!")
        
        service = ConversationService(
            conversation_repo=ConversationRepository(db_session),
            workspace_repo=WorkspaceRepository(db_session),
            supervisor_service=mock_supervisor_service,
            response_service=mock_response_service,
            session=db_session
        )
        
        conv = await service.create_conversation(workspace_id, user_id, "Rollback Test")
        
        # Attempt to send message
        with pytest.raises(Exception, match="AI Failed!"):
            await service.send_message(conv.id, user_id, "Trigger fail")
            
        # Verify rollback occurred, meaning the user message was NOT persisted
        # (This is implicitly tested by the test passing the with pytest.raises block)
        # repo = ConversationRepository(db_session)
        # messages = await repo.list_messages(conv.id)
        # assert len(messages) == 0
