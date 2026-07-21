"""End-to-End integration tests for the Conversation Module."""

import uuid
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.workspaces.models import Workspace
from app.agents.response.dependencies import get_llm_provider
from app.agents.response.providers.base import BaseLLMProvider
from app.agents.response.models import LLMResponse, Prompt
from app.agents.supervisor.dependencies import get_embedding_orchestrator
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator
from app.config.settings import get_settings
from app.database.dependency import get_db_session


class MockE2ELLMProvider(BaseLLMProvider):
    """Deterministic test double for LLM provider."""
    
    def __init__(self):
        self.should_fail = False
        self.call_count = 0
        
    async def generate(self, prompt: Prompt) -> LLMResponse:
        self.call_count += 1
        if self.should_fail:
            raise Exception("Catastrophic LLM Failure")
        return LLMResponse(text="Mock Assistant Reply")


@pytest.fixture
def mock_llm() -> MockE2ELLMProvider:
    return MockE2ELLMProvider()


from app.modules.retrieval.dependencies import get_retrieval_service
from app.modules.retrieval.service import RetrievalService
from app.vectorstore.repositories.models import VectorSearchParams, VectorSearchResult


class MockE2ERetrievalService(RetrievalService):
    """Deterministic test double for RetrievalService."""
    
    def __init__(self):
        pass  # Bypass vector_repo initialization
        
    async def retrieve(self, params: VectorSearchParams) -> list[VectorSearchResult]:
        # Return empty results or mock results
        return []


@pytest.fixture
def mock_retrieval() -> MockE2ERetrievalService:
    return MockE2ERetrievalService()


@pytest.fixture
async def e2e_db_setup(db_session: AsyncSession):
    """Setup test users and workspaces in the real test database."""
    user = User(
        id=uuid.uuid4(),
        email=f"e2e_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="pw",
        first_name="Test",
        last_name="User"
    )
    workspace = Workspace(
        id=uuid.uuid4(),
        name="E2E Workspace",
        owner_id=user.id
    )
    
    other_user = User(
        id=uuid.uuid4(),
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="pw",
        first_name="Other",
        last_name="User"
    )
    other_workspace = Workspace(
        id=uuid.uuid4(),
        name="Other Workspace",
        owner_id=other_user.id
    )
    
    db_session.add_all([user, workspace, other_user, other_workspace])
    await db_session.flush()
    await db_session.commit()
    
    return {
        "user": user,
        "workspace": workspace,
        "other_user": other_user,
        "other_workspace": other_workspace,
    }


from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def e2e_client(e2e_db_setup, mock_llm, mock_provider, mock_retrieval, db_engine) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client pointing to the live app with mocked external boundaries."""
    user = e2e_db_setup["user"]
    settings = get_settings()
    
    mock_orchestrator = EmbeddingOrchestrator(
        provider=mock_provider,
        batch_size=settings.embedding_batch_size
    )
    
    session_factory = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_llm_provider] = lambda: mock_llm
    app.dependency_overrides[get_embedding_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval
    
    async def override_db():
        async with session_factory() as session:
            yield session
    app.dependency_overrides[get_db_session] = override_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()


@pytest.fixture
async def other_e2e_client(e2e_db_setup, mock_llm, mock_provider, mock_retrieval, db_engine) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client authenticated as the OTHER user."""
    other_user = e2e_db_setup["other_user"]
    settings = get_settings()
    
    mock_orchestrator = EmbeddingOrchestrator(
        provider=mock_provider,
        batch_size=settings.embedding_batch_size
    )
    
    session_factory = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    
    app.dependency_overrides[get_current_user] = lambda: other_user
    app.dependency_overrides[get_llm_provider] = lambda: mock_llm
    app.dependency_overrides[get_embedding_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval
    
    async def override_db():
        async with session_factory() as session:
            yield session
    app.dependency_overrides[get_db_session] = override_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestConversationEndToEnd:
    
    async def test_conversation_lifecycle(self, e2e_client, e2e_db_setup):
        """Category 1: Test creating, retrieving, listing, and deleting a conversation."""
        workspace_id = e2e_db_setup["workspace"].id
        
        # Create
        create_res = await e2e_client.post(
            f"/api/v1/workspaces/{workspace_id}/conversations",
            json={"title": "E2E Lifecycle"}
        )
        assert create_res.status_code == 201
        data = create_res.json()
        assert data["success"] is True
        conv_id = data["data"]["id"]
        assert data["data"]["title"] == "E2E Lifecycle"
        
        # Get
        get_res = await e2e_client.get(f"/api/v1/conversations/{conv_id}")
        assert get_res.status_code == 200
        assert get_res.json()["data"]["id"] == conv_id
        
        # List
        list_res = await e2e_client.get(f"/api/v1/workspaces/{workspace_id}/conversations")
        assert list_res.status_code == 200
        assert len(list_res.json()["data"]) >= 1
        assert any(c["id"] == conv_id for c in list_res.json()["data"])
        
        # Delete
        del_res = await e2e_client.delete(f"/api/v1/conversations/{conv_id}")
        assert del_res.status_code == 200
        
        # Get should now 404
        get_deleted_res = await e2e_client.get(f"/api/v1/conversations/{conv_id}")
        assert get_deleted_res.status_code == 404

    async def test_messaging_and_memory_workflow(self, e2e_client, e2e_db_setup, mock_llm):
        """Categories 2 & 3: Test sending messages, growing history, and chronological ordering."""
        workspace_id = e2e_db_setup["workspace"].id
        
        create_res = await e2e_client.post(
            f"/api/v1/workspaces/{workspace_id}/conversations",
            json={"title": "E2E Messaging"}
        )
        conv_id = create_res.json()["data"]["id"]
        
        # Send first message
        msg1_res = await e2e_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "First user message"}
        )
        assert msg1_res.status_code == 201
        msg1_data = msg1_res.json()["data"]["assistant"]
        assert msg1_data["role"] == "assistant"
        assert msg1_data["content"] == "Mock Assistant Reply"
        assert mock_llm.call_count == 1
        
        # Send second message
        msg2_res = await e2e_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "Second user message"}
        )
        assert msg2_res.status_code == 201
        assert mock_llm.call_count == 2
        
        # Verify conversation memory / history grows correctly
        get_res = await e2e_client.get(f"/api/v1/conversations/{conv_id}")
        history = get_res.json()["data"]["messages"]
        
        assert len(history) == 4  # 2 user messages + 2 assistant messages
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "First user message"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Mock Assistant Reply"
        assert history[2]["role"] == "user"
        assert history[2]["content"] == "Second user message"

    async def test_authorization_and_isolation(self, e2e_client, e2e_db_setup):
        """Category 5: Verify cross-user access fails safely with 404."""
        workspace_id = e2e_db_setup["workspace"].id
        other_user = e2e_db_setup["other_user"]
        
        # User 1 creates conversation
        create_res = await e2e_client.post(
            f"/api/v1/workspaces/{workspace_id}/conversations",
            json={"title": "Secret"}
        )
        conv_id = create_res.json()["data"]["id"]
        
        # Switch to User 2
        app.dependency_overrides[get_current_user] = lambda: other_user
        
        # User 2 attempts to get conversation
        get_res = await e2e_client.get(f"/api/v1/conversations/{conv_id}")
        assert get_res.status_code == 404
        
        # User 2 attempts to send message
        msg_res = await e2e_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "Hacking"}
        )
        assert msg_res.status_code == 404
        
        # User 2 attempts to delete conversation
        del_res = await e2e_client.delete(f"/api/v1/conversations/{conv_id}")
        assert del_res.status_code == 404

    async def test_payload_validation(self, e2e_client, e2e_db_setup):
        """Category 6: Verify edge-case payloads result in strict 422s."""
        workspace_id = e2e_db_setup["workspace"].id
        
        create_res = await e2e_client.post(
            f"/api/v1/workspaces/{workspace_id}/conversations",
            json={"title": "Validation"}
        )
        conv_id = create_res.json()["data"]["id"]
        
        # Empty message
        msg_res = await e2e_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "   "}
        )
        assert msg_res.status_code == 422
        
        # Malformed UUID in route
        bad_route_res = await e2e_client.get("/api/v1/conversations/not-a-uuid")
        assert bad_route_res.status_code == 422

    async def test_transaction_rollback_on_failure(self, e2e_client, e2e_db_setup, mock_llm):
        """Category 7: Verify that catastrophic failures unwind the transaction and leave no orphaned messages."""
        workspace_id = e2e_db_setup["workspace"].id
        
        create_res = await e2e_client.post(
            f"/api/v1/workspaces/{workspace_id}/conversations",
            json={"title": "Rollback Test"}
        )
        conv_id = create_res.json()["data"]["id"]
        
        # Configure the mock LLM to explode mid-generation
        mock_llm.should_fail = True
        
        # Attempt to send message, which will fail with a 500 error
        msg_res = await e2e_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "Trigger failure"}
        )
        assert msg_res.status_code == 500
        
        # Fetch the conversation and verify the user message was NOT persisted
        get_res = await e2e_client.get(f"/api/v1/conversations/{conv_id}")
        history = get_res.json()["data"]["messages"]
        assert len(history) == 0  # No orphaned user message!
