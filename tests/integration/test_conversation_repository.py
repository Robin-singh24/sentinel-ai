import asyncio
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import SentinelNotFoundError
from app.modules.conversations.models import Conversation, Message, MessageRole
from app.modules.conversations.repository import ConversationRepository
from app.modules.auth.models import User
from app.modules.workspaces.models import Workspace

@pytest.fixture
async def setup_db(db_session: AsyncSession):
    # Setup standard user and workspace
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    user = User(
        id=user_id, 
        email=f"test_{user_id}@example.com", 
        password_hash="pw",
        first_name="Test",
        last_name="User"
    )
    workspace = Workspace(id=workspace_id, name="Test Workspace", owner_id=user_id)

    db_session.add_all([user, workspace])
    await db_session.flush()
    
    return {"user_id": user_id, "workspace_id": workspace_id}

@pytest.mark.asyncio
class TestConversationRepository:

    async def test_create_and_get_by_id(self, db_session: AsyncSession, setup_db):
        repo = ConversationRepository(db_session)
        user_id = setup_db["user_id"]
        workspace_id = setup_db["workspace_id"]
        
        # Create
        conv = Conversation(
            workspace_id=workspace_id,
            user_id=user_id,
            title="Test Conversation"
        )
        created_conv = await repo.create(conv)
        assert created_conv.id is not None
        assert created_conv.title == "Test Conversation"
        
        # Get by ID
        fetched_conv = await repo.get_by_id(created_conv.id)
        assert fetched_conv.id == created_conv.id
        
        # Error case
        with pytest.raises(SentinelNotFoundError):
            await repo.get_by_id(uuid.uuid4())

    async def test_messages_create_list_and_eager_loading(self, db_session: AsyncSession, setup_db):
        repo = ConversationRepository(db_session)
        user_id = setup_db["user_id"]
        workspace_id = setup_db["workspace_id"]
        
        conv = Conversation(workspace_id=workspace_id, user_id=user_id)
        await repo.create(conv)
        
        # Insert out of order
        now = datetime.now(timezone.utc)
        
        msg2 = Message(
            conversation_id=conv.id,
            role=MessageRole.assistant,
            content="Second",
            created_at=now + timedelta(seconds=1)
        )
        msg1 = Message(
            conversation_id=conv.id,
            role=MessageRole.user,
            content="First",
            created_at=now
        )
        
        await repo.create_message(msg2)
        await repo.create_message(msg1)
        
        # List messages explicitly
        messages = await repo.list_messages(conv.id)
        assert len(messages) == 2
        # Ordering guarantee: oldest first
        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        
        # Test eager loading (Note: eager loading itself doesn't guarantee order, but ensures relationship is loaded)
        db_session.expunge_all() # Clear cache to test eager load
        fetched_conv = await repo.get_by_id(conv.id, include_messages=True)
        assert len(fetched_conv.messages) == 2

    async def test_list_by_workspace_ordering(self, db_session: AsyncSession, setup_db):
        repo = ConversationRepository(db_session)
        user_id = setup_db["user_id"]
        workspace_id = setup_db["workspace_id"]
        
        now = datetime.now(timezone.utc)
        
        conv1 = Conversation(workspace_id=workspace_id, user_id=user_id, updated_at=now)
        conv2 = Conversation(workspace_id=workspace_id, user_id=user_id, updated_at=now + timedelta(seconds=1))
        
        await repo.create(conv1)
        await repo.create(conv2)
        
        convs = await repo.list_by_workspace(workspace_id, user_id)
        assert len(convs) == 2
        # Ordering guarantee: newest first (updated_at DESC)
        assert convs[0].id == conv2.id
        assert convs[1].id == conv1.id

    async def test_delete(self, db_session: AsyncSession, setup_db):
        repo = ConversationRepository(db_session)
        user_id = setup_db["user_id"]
        workspace_id = setup_db["workspace_id"]
        
        conv = Conversation(workspace_id=workspace_id, user_id=user_id)
        await repo.create(conv)
        
        # Delete
        await repo.delete(conv)
        await db_session.flush() # Force deletion to db
        
        # Verify
        with pytest.raises(SentinelNotFoundError):
            await repo.get_by_id(conv.id)
