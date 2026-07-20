"""Unit tests for the Conversation Memory Service."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.common.exceptions import SentinelNotFoundError
from app.config.settings import Settings
from app.modules.auth.models import User  # noqa: F401
from app.modules.conversations.models import Conversation, Message, MessageRole
from app.modules.conversations.repository import ConversationRepository
from app.modules.documents.models import Document  # noqa: F401
from app.modules.memory.exceptions import SentinelMemoryError
from app.modules.memory.models import ConversationMemory, MemoryRole
from app.modules.memory.service import ConversationMemoryService
from app.modules.workspaces.models import Workspace  # noqa: F401
from sqlalchemy.exc import OperationalError


@pytest.fixture
def mock_repository():
    """Mock the ConversationRepository."""
    return AsyncMock(spec=ConversationRepository)

@pytest.fixture
def mock_settings():
    """Mock the Settings object."""
    settings = Settings()
    settings.memory_window_size = 20
    return settings


@pytest.fixture
def service(mock_repository, mock_settings):
    """Instantiate the ConversationMemoryService with the mock repository and settings."""
    return ConversationMemoryService(repository=mock_repository, settings=mock_settings)


class TestConversationMemoryService:
    """Tests for conversation memory persistence orchestration."""

    @pytest.mark.asyncio
    async def test_get_memory_successful_retrieval(self, service, mock_repository):
        """Verify successful retrieval and accurate ORM-to-domain mapping."""
        convo_id = uuid.uuid4()
        
        # Create out-of-order ORM messages to verify chronological sorting
        base_time = datetime.now(UTC)
        msg_new = Message(
            id=uuid.uuid4(),
            role=MessageRole.assistant,
            content="I am fine.",
            created_at=base_time + timedelta(minutes=1)
        )
        msg_old = Message(
            id=uuid.uuid4(),
            role=MessageRole.user,
            content="How are you?",
            created_at=base_time
        )
        
        mock_convo = Conversation(id=convo_id, messages=[msg_new, msg_old])
        mock_repository.get_conversation_with_messages.return_value = mock_convo
        
        memory = await service.get_memory(convo_id)
        
        assert isinstance(memory, ConversationMemory)
        assert len(memory.messages) == 2
        
        # Verify chronological ordering (oldest first)
        assert memory.messages[0].role == MemoryRole.USER
        assert memory.messages[0].content == "How are you?"
        
        assert memory.messages[1].role == MemoryRole.ASSISTANT
        assert memory.messages[1].content == "I am fine."
        
        mock_repository.get_conversation_with_messages.assert_called_once_with(convo_id)

    @pytest.mark.asyncio
    async def test_get_memory_empty_conversation(self, service, mock_repository):
        """Verify that an existing conversation with no messages returns empty memory."""
        convo_id = uuid.uuid4()
        
        mock_convo = Conversation(id=convo_id, messages=[])
        mock_repository.get_conversation_with_messages.return_value = mock_convo
        
        memory = await service.get_memory(convo_id)
        
        assert isinstance(memory, ConversationMemory)
        assert len(memory.messages) == 0

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, service, mock_repository):
        """Verify SentinelNotFoundError propagates transparently when repo raises it."""
        convo_id = uuid.uuid4()
        mock_repository.get_conversation_with_messages.side_effect = SentinelNotFoundError(
            resource="conversation", identifier=str(convo_id)
        )
        
        with pytest.raises(SentinelNotFoundError) as exc_info:
            await service.get_memory(convo_id)
            
        assert "conversation with identifier" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_memory_sqlalchemy_error_wrapping(self, service, mock_repository):
        """Verify SQLAlchemy errors are wrapped in SentinelMemoryError."""
        convo_id = uuid.uuid4()
        mock_repository.get_conversation_with_messages.side_effect = OperationalError(
            "SELECT 1", {}, None
        )
        
        with pytest.raises(
            SentinelMemoryError, 
            match="Failed to retrieve conversation memory from the database."
        ):
            await service.get_memory(convo_id)

    @pytest.mark.asyncio
    async def test_get_memory_unexpected_error_wrapping(self, service, mock_repository):
        """Verify unexpected errors are caught and wrapped securely."""
        convo_id = uuid.uuid4()
        mock_repository.get_conversation_with_messages.side_effect = ValueError("Some weird error")
        
        with pytest.raises(
            SentinelMemoryError, 
            match="An unexpected error occurred retrieving memory."
        ):
            await service.get_memory(convo_id)

    @pytest.mark.asyncio
    async def test_get_memory_cancellation_propagation(self, service, mock_repository):
        """Verify asyncio.CancelledError is re-raised untouched."""
        convo_id = uuid.uuid4()
        mock_repository.get_conversation_with_messages.side_effect = asyncio.CancelledError()
        
        with pytest.raises(asyncio.CancelledError):
            await service.get_memory(convo_id)

    @pytest.mark.asyncio
    async def test_enum_translation_integrity(self, service, mock_repository):
        """Explicitly test translation of every persistence role to every domain role."""
        convo_id = uuid.uuid4()
        base_time = datetime.now(UTC)
        
        messages = [
            Message(role=MessageRole.system, content="1", created_at=base_time),
            Message(
                role=MessageRole.user, 
                content="2", 
                created_at=base_time + timedelta(seconds=1)
            ),
            Message(
                role=MessageRole.assistant, 
                content="3", 
                created_at=base_time + timedelta(seconds=2)
            )
        ]
        
        mock_convo = Conversation(id=convo_id, messages=messages)
        mock_repository.get_conversation_with_messages.return_value = mock_convo
        
        memory = await service.get_memory(convo_id)
        
        assert len(memory.messages) == 3
        assert memory.messages[0].role == MemoryRole.SYSTEM
        assert memory.messages[1].role == MemoryRole.USER
        assert memory.messages[2].role == MemoryRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_get_memory_window_smaller_than_conversation(
        self, service, mock_repository, mock_settings
    ):
        """Verify memory is properly truncated when it exceeds window size."""
        convo_id = uuid.uuid4()
        mock_settings.memory_window_size = 2
        
        base_time = datetime.now(UTC)
        messages = [
            Message(role=MessageRole.user, content="1", created_at=base_time),
            Message(
                role=MessageRole.assistant, 
                content="2", 
                created_at=base_time + timedelta(seconds=1)
            ),
            Message(
                role=MessageRole.user, 
                content="3", 
                created_at=base_time + timedelta(seconds=2)
            ),
            Message(
                role=MessageRole.assistant, 
                content="4", 
                created_at=base_time + timedelta(seconds=3)
            )
        ]
        
        mock_repository.get_conversation_with_messages.return_value = Conversation(
            id=convo_id, messages=messages
        )
        
        memory = await service.get_memory(convo_id)
        
        # Only the last 2 should be kept
        assert len(memory.messages) == 2
        assert memory.messages[0].content == "3"
        assert memory.messages[1].content == "4"

    @pytest.mark.asyncio
    async def test_get_memory_window_equal_to_conversation(
        self, service, mock_repository, mock_settings
    ):
        """Verify memory is kept intact when exactly matching window size."""
        convo_id = uuid.uuid4()
        mock_settings.memory_window_size = 2
        
        base_time = datetime.now(UTC)
        messages = [
            Message(role=MessageRole.user, content="1", created_at=base_time),
            Message(
                role=MessageRole.assistant, 
                content="2", 
                created_at=base_time + timedelta(seconds=1)
            )
        ]
        
        mock_repository.get_conversation_with_messages.return_value = Conversation(
            id=convo_id, messages=messages
        )
        
        memory = await service.get_memory(convo_id)
        
        assert len(memory.messages) == 2
        assert memory.messages[0].content == "1"
        assert memory.messages[1].content == "2"

    @pytest.mark.asyncio
    async def test_get_memory_window_size_one(
        self, service, mock_repository, mock_settings
    ):
        """Verify window size of 1 correctly keeps only the latest message."""
        convo_id = uuid.uuid4()
        mock_settings.memory_window_size = 1
        
        base_time = datetime.now(UTC)
        messages = [
            Message(role=MessageRole.user, content="1", created_at=base_time),
            Message(
                role=MessageRole.assistant, 
                content="2", 
                created_at=base_time + timedelta(seconds=1)
            )
        ]
        
        mock_repository.get_conversation_with_messages.return_value = Conversation(
            id=convo_id, messages=messages
        )
        
        memory = await service.get_memory(convo_id)
        
        assert len(memory.messages) == 1
        assert memory.messages[0].content == "2"
