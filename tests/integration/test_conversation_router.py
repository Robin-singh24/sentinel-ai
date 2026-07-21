import pytest
import uuid
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.main import app

from app.common.exceptions import SentinelNotFoundError
from app.modules.conversations.models import Conversation, Message, MessageRole
from app.modules.conversations.service import ConversationService
from app.modules.conversations.dependencies import get_conversation_service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from datetime import datetime, timezone


@pytest.fixture
def mock_current_user():
    return User(
        id=uuid.uuid4(),
        email="router_test@example.com",
        first_name="Router",
        last_name="Test"
    )

from unittest.mock import AsyncMock

@pytest.fixture
def mock_conversation_service():
    return AsyncMock(spec=ConversationService)


@pytest.fixture
def test_app(mock_current_user, mock_conversation_service):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    yield app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestConversationRouter:
    async def test_list_conversations(self, test_app, mock_conversation_service, mock_current_user):
        workspace_id = uuid.uuid4()
        conv_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        
        mock_conversation_service.list_conversations.return_value = [
            Conversation(id=conv_id, title="Test", created_at=now, updated_at=now)
        ]
        
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/workspaces/{workspace_id}/conversations")
            
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(conv_id)
        mock_conversation_service.list_conversations.assert_awaited_once_with(
            workspace_id=workspace_id,
            owner_id=mock_current_user.id
        )

    async def test_create_conversation(self, test_app, mock_conversation_service, mock_current_user):
        workspace_id = uuid.uuid4()
        conv_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        
        mock_conversation_service.create_conversation.return_value = Conversation(
            id=conv_id, title="New", created_at=now, updated_at=now, messages=[]
        )
        
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/workspaces/{workspace_id}/conversations",
                json={"title": "New"}
            )
            
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(conv_id)
        mock_conversation_service.create_conversation.assert_awaited_once_with(
            workspace_id=workspace_id,
            owner_id=mock_current_user.id,
            title="New"
        )

    async def test_get_conversation(self, test_app, mock_conversation_service, mock_current_user):
        conv_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        
        mock_conversation_service.get_conversation.return_value = Conversation(
            id=conv_id, title="Get Me", created_at=now, updated_at=now, messages=[]
        )
        
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/conversations/{conv_id}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Get Me"
        assert data["data"]["messages"] == []
        mock_conversation_service.get_conversation.assert_awaited_once_with(
            conversation_id=conv_id,
            owner_id=mock_current_user.id
        )
        
    async def test_get_conversation_not_found(self, test_app, mock_conversation_service, mock_current_user):
        conv_id = uuid.uuid4()
        
        # Simulate global exception handler catching domain error
        mock_conversation_service.get_conversation.side_effect = SentinelNotFoundError(
            resource="Conversation", identifier=str(conv_id)
        )
        
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/conversations/{conv_id}")
            
        # Exception handler should turn it into a 404
        assert response.status_code == 404

    async def test_delete_conversation(self, test_app, mock_conversation_service, mock_current_user):
        conv_id = uuid.uuid4()
        
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.delete(f"/api/v1/conversations/{conv_id}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None
        mock_conversation_service.delete_conversation.assert_awaited_once_with(
            conversation_id=conv_id,
            owner_id=mock_current_user.id
        )

    async def test_send_message(self, test_app, mock_conversation_service, mock_current_user):
        conv_id = uuid.uuid4()
        msg_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        
        mock_conversation_service.send_message.return_value = Message(
            id=msg_id, conversation_id=conv_id, role=MessageRole.assistant,
            content="I am AI", created_at=now
        )
        
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/conversations/{conv_id}/messages",
                json={"content": "Hello"}
            )
            
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["assistant"]["content"] == "I am AI"
        assert data["data"]["assistant"]["role"] == "assistant"
        mock_conversation_service.send_message.assert_awaited_once_with(
            conversation_id=conv_id,
            owner_id=mock_current_user.id,
            content="Hello"
        )
