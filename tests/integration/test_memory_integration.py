"""End-to-End integration tests for Conversation Memory orchestration."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.agents.response.exceptions import SentinelResponseError
from app.agents.response.formatter import ContextFormatter
from app.agents.response.models import GeneratedResponse, LLMResponse, Prompt
from app.agents.response.parser import ResponseParser
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.providers.base import BaseLLMProvider
from app.agents.response.service import ResponseService
from app.agents.supervisor.models import WorkflowExecutionResult
from app.common.exceptions import SentinelNotFoundError
from app.config.settings import Settings
from app.modules.auth.models import User
from app.modules.conversations.models import Conversation, Message, MessageRole
from app.modules.conversations.repository import ConversationRepository
from app.modules.memory.formatter import MemoryFormatter
from app.modules.memory.service import ConversationMemoryService
from app.modules.workspaces.models import Workspace
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def setup_test_data(db_session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    """Sets up required Foreign Key references: User and Workspace."""
    user = User(
        id=uuid.uuid4(),
        email="test_memory@sentinel.ai",
        password_hash="fake",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    workspace = Workspace(
        id=uuid.uuid4(),
        name="Memory Test Workspace",
        description="Testing memory",
        owner_id=user.id,
    )
    db_session.add(user)
    db_session.add(workspace)
    await db_session.commit()
    return user.id, workspace.id


@pytest.fixture
def mock_provider() -> AsyncMock:
    """Provides a mocked LLM Provider."""
    provider = AsyncMock(spec=BaseLLMProvider)
    provider.generate.return_value = LLMResponse(text="Mocked LLM Response")
    return provider


@pytest.fixture
def test_settings() -> Settings:
    """Provides consistent settings for tests with a known window size."""
    settings = Settings()
    settings.memory_window_size = 3
    return settings


@pytest.fixture
def repository(db_session: AsyncSession) -> ConversationRepository:
    """Provides the ConversationRepository bound to the test session."""
    return ConversationRepository(session=db_session)


@pytest.fixture
def memory_service(
    repository: ConversationRepository, test_settings: Settings
) -> ConversationMemoryService:
    """Provides the ConversationMemoryService."""
    return ConversationMemoryService(repository=repository, settings=test_settings)


@pytest.fixture
def response_service(
    mock_provider: AsyncMock,
    memory_service: ConversationMemoryService
) -> ResponseService:
    """Provides the fully orchestrated ResponseService."""
    return ResponseService(
        formatter=ContextFormatter(),
        prompt_builder=PromptBuilder(),
        llm_provider=mock_provider,
        parser=ResponseParser(),
        memory_service=memory_service,
        memory_formatter=MemoryFormatter()
    )


class TestMemoryIntegration:
    """E2E integration tests for memory retrieval and formatting."""

    @pytest.mark.asyncio
    async def test_happy_path(
        self,
        db_session: AsyncSession,
        setup_test_data,
        response_service,
        mock_provider,
        test_settings,
    ):
        """Verify standard conversation is retrieved, formatted, and sent to LLM correctly."""
        user_id, workspace_id = setup_test_data
        
        # We use window size 3. We'll add 2 messages.
        convo_id = uuid.uuid4()
        convo = Conversation(id=convo_id, workspace_id=workspace_id, user_id=user_id)
        msg1 = Message(conversation_id=convo_id, role=MessageRole.user, content="Hello")
        msg2 = Message(conversation_id=convo_id, role=MessageRole.assistant, content="Hi there")
        
        db_session.add(convo)
        db_session.add_all([msg1, msg2])
        await db_session.commit()
        
        result = await response_service.generate_response(
            query="What next?", 
            workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
            conversation_id=convo_id
        )
        
        assert isinstance(result, GeneratedResponse)
        
        # Verify the prompt structure
        mock_provider.generate.assert_called_once()
        prompt: Prompt = mock_provider.generate.call_args[0][0]
        
        assert "--- CONVERSATION MEMORY ---" in prompt.user_prompt
        assert "User: Hello" in prompt.user_prompt
        assert "Assistant: Hi there" in prompt.user_prompt

    @pytest.mark.asyncio
    async def test_empty_conversation(
        self, db_session: AsyncSession, setup_test_data, response_service, mock_provider
    ):
        """Verify an existing conversation with zero messages handles cleanly."""
        user_id, workspace_id = setup_test_data
        
        convo_id = uuid.uuid4()
        convo = Conversation(id=convo_id, workspace_id=workspace_id, user_id=user_id)
        
        db_session.add(convo)
        await db_session.commit()
        
        await response_service.generate_response(
            query="Test query", 
            workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
            conversation_id=convo_id
        )
        
        prompt: Prompt = mock_provider.generate.call_args[0][0]
        assert "--- CONVERSATION MEMORY ---" in prompt.user_prompt
        assert "User:" not in prompt.user_prompt.split("--- CONVERSATION MEMORY ---")[1]

    @pytest.mark.asyncio
    async def test_memory_window(
        self, db_session: AsyncSession, setup_test_data, response_service, mock_provider
    ):
        """Verify older messages are truncated if conversation exceeds default window size (3)."""
        user_id, workspace_id = setup_test_data
        
        convo_id = uuid.uuid4()
        convo = Conversation(id=convo_id, workspace_id=workspace_id, user_id=user_id)
        
        msgs = [
            Message(conversation_id=convo_id, role=MessageRole.user, content="Msg 1"),
            Message(conversation_id=convo_id, role=MessageRole.assistant, content="Msg 2"),
            Message(conversation_id=convo_id, role=MessageRole.user, content="Msg 3"),
            Message(conversation_id=convo_id, role=MessageRole.assistant, content="Msg 4"),
        ]
        
        db_session.add(convo)
        db_session.add_all(msgs)
        await db_session.commit()
        
        await response_service.generate_response(
            query="Query", 
            workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
            conversation_id=convo_id
        )
        
        prompt: Prompt = mock_provider.generate.call_args[0][0]
        
        assert "Msg 1" not in prompt.user_prompt
        assert "Msg 2" in prompt.user_prompt
        assert "Msg 3" in prompt.user_prompt
        assert "Msg 4" in prompt.user_prompt

    @pytest.mark.asyncio
    async def test_configurable_window_size(
        self, db_session: AsyncSession, setup_test_data, repository, mock_provider, test_settings
    ):
        """Verify window truncates based precisely on configuration at runtime."""
        user_id, workspace_id = setup_test_data
        
        # Override settings for this test only
        test_settings.memory_window_size = 2
        custom_memory_service = ConversationMemoryService(repository, test_settings)
        
        custom_response_service = ResponseService(
            formatter=ContextFormatter(),
            prompt_builder=PromptBuilder(),
            llm_provider=mock_provider,
            parser=ResponseParser(),
            memory_service=custom_memory_service,
            memory_formatter=MemoryFormatter()
        )
        
        convo_id = uuid.uuid4()
        convo = Conversation(id=convo_id, workspace_id=workspace_id, user_id=user_id)
        
        msgs = [
            Message(conversation_id=convo_id, role=MessageRole.user, content="old_msg"),
            Message(conversation_id=convo_id, role=MessageRole.assistant, content="kept_msg1"),
            Message(conversation_id=convo_id, role=MessageRole.user, content="kept_msg2"),
        ]
        
        db_session.add(convo)
        db_session.add_all(msgs)
        await db_session.commit()
        
        await custom_response_service.generate_response(
            query="Query", 
            workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
            conversation_id=convo_id
        )
        
        prompt: Prompt = mock_provider.generate.call_args[0][0]
        assert "old_msg" not in prompt.user_prompt
        assert "kept_msg1" in prompt.user_prompt
        assert "kept_msg2" in prompt.user_prompt

    @pytest.mark.asyncio
    async def test_conversation_not_found(
        self, response_service, mock_provider
    ):
        """Verify invalid conversation ID correctly bubbles up SentinelNotFoundError via wrapper."""
        invalid_convo_id = uuid.uuid4()
        
        with pytest.raises(SentinelResponseError) as exc_info:
            await response_service.generate_response(
                query="Query", 
                workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
                conversation_id=invalid_convo_id
            )
            
        assert isinstance(exc_info.value.__cause__, SentinelNotFoundError)
        mock_provider.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_role_translation(
        self, db_session: AsyncSession, setup_test_data, response_service, mock_provider
    ):
        """Verify SYSTEM, USER, and ASSISTANT roles persist and format exactly as expected."""
        user_id, workspace_id = setup_test_data
        
        convo_id = uuid.uuid4()
        convo = Conversation(id=convo_id, workspace_id=workspace_id, user_id=user_id)
        
        msgs = [
            Message(conversation_id=convo_id, role=MessageRole.system, content="Initialize"),
            Message(conversation_id=convo_id, role=MessageRole.user, content="Query"),
            Message(conversation_id=convo_id, role=MessageRole.assistant, content="Answer"),
        ]
        
        db_session.add(convo)
        db_session.add_all(msgs)
        await db_session.commit()
        
        await response_service.generate_response(
            query="Next", 
            workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
            conversation_id=convo_id
        )
        
        prompt: Prompt = mock_provider.generate.call_args[0][0]
        memory_block = prompt.user_prompt.split("--- CONVERSATION MEMORY ---")[1]
        
        assert "System: Initialize" in memory_block
        assert "User: Query" in memory_block
        assert "Assistant: Answer" in memory_block

    @pytest.mark.asyncio
    async def test_chronological_ordering(
        self, db_session: AsyncSession, setup_test_data, response_service, mock_provider
    ):
        """Verify messages are strictly ordered by created_at regardless of insertion order."""
        user_id, workspace_id = setup_test_data
        
        convo_id = uuid.uuid4()
        convo = Conversation(id=convo_id, workspace_id=workspace_id, user_id=user_id)
        db_session.add(convo)
        
        base_time = datetime.now(UTC)
        
        # Insert out of order
        msg_latest = Message(
            conversation_id=convo_id, role=MessageRole.assistant, 
            content="latest_msg", created_at=base_time + timedelta(seconds=10)
        )
        msg_oldest = Message(
            conversation_id=convo_id, role=MessageRole.user, 
            content="oldest_msg", created_at=base_time
        )
        msg_middle = Message(
            conversation_id=convo_id, role=MessageRole.assistant, 
            content="middle_msg", created_at=base_time + timedelta(seconds=5)
        )
        
        db_session.add_all([msg_latest, msg_oldest, msg_middle])
        await db_session.commit()
        
        await response_service.generate_response(
            query="Q", 
            workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
            conversation_id=convo_id
        )
        
        prompt: Prompt = mock_provider.generate.call_args[0][0]
        memory_block = prompt.user_prompt.split("--- CONVERSATION MEMORY ---")[1]
        
        pos_oldest = memory_block.find("oldest_msg")
        pos_middle = memory_block.find("middle_msg")
        pos_latest = memory_block.find("latest_msg")
        
        assert pos_oldest < pos_middle < pos_latest

    @pytest.mark.asyncio
    async def test_long_conversation(
        self,
        db_session: AsyncSession,
        setup_test_data,
        response_service,
        mock_provider,
        test_settings,
    ):
        """Verify massive conversations don't break formatting or blow up the prompt."""
        user_id, workspace_id = setup_test_data
        
        convo_id = uuid.uuid4()
        convo = Conversation(id=convo_id, workspace_id=workspace_id, user_id=user_id)
        db_session.add(convo)
        
        base_time = datetime.now(UTC)
        # Create 50 messages
        msgs = [
            Message(
                conversation_id=convo_id, 
                role=MessageRole.user if i % 2 == 0 else MessageRole.assistant,
                content=f"massive_msg_{i}",
                created_at=base_time + timedelta(seconds=i)
            )
            for i in range(50)
        ]
        db_session.add_all(msgs)
        await db_session.commit()
        
        await response_service.generate_response(
            query="Q", 
            workflow_result=WorkflowExecutionResult(retrieved_chunks=[]),
            conversation_id=convo_id
        )
        
        prompt: Prompt = mock_provider.generate.call_args[0][0]
        memory_block = prompt.user_prompt.split("--- CONVERSATION MEMORY ---")[1]
        
        # Only the last 3 should be kept (window size = 3)
        assert "massive_msg_0" not in memory_block
        assert "massive_msg_46" not in memory_block
        assert "massive_msg_47" in memory_block
        assert "massive_msg_48" in memory_block
        assert "massive_msg_49" in memory_block
