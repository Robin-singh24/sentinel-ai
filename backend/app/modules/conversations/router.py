"""Conversation API endpoints — routing and transport adapter."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.common.responses import SuccessResponse
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.conversations.dependencies import get_conversation_service
from app.modules.conversations.schemas import (
    ConversationResponse,
    ConversationSummaryResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.modules.conversations.service import ConversationService

router = APIRouter(tags=["Conversations"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[ConversationService, Depends(get_conversation_service)]


@router.get(
    "/workspaces/{workspace_id}/conversations",
    response_model=SuccessResponse[list[ConversationSummaryResponse]],
    summary="List all conversations in a workspace",
)
async def list_conversations(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[list[ConversationSummaryResponse]]:
    """Return all conversations belonging to the specified workspace."""
    conversations = await service.list_conversations(
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )
    return SuccessResponse(
        data=[ConversationSummaryResponse.model_validate(c) for c in conversations]
    )


@router.post(
    "/workspaces/{workspace_id}/conversations",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[ConversationResponse],
    summary="Create a new conversation in a workspace",
)
async def create_conversation(
    workspace_id: uuid.UUID,
    request: CreateConversationRequest,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[ConversationResponse]:
    """Create a new conversation for the authenticated user."""
    conversation = await service.create_conversation(
        workspace_id=workspace_id,
        owner_id=current_user.id,
        title=request.title,
    )
    return SuccessResponse(data=ConversationResponse.model_validate(conversation))


@router.get(
    "/conversations/{conversation_id}",
    response_model=SuccessResponse[ConversationResponse],
    summary="Get a conversation by ID",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[ConversationResponse]:
    """Return a single conversation and its messages."""
    conversation = await service.get_conversation(
        conversation_id=conversation_id,
        owner_id=current_user.id,
    )
    return SuccessResponse(data=ConversationResponse.model_validate(conversation))


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[None],
    summary="Delete a conversation",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[None]:
    """Delete an owned conversation."""
    await service.delete_conversation(
        conversation_id=conversation_id,
        owner_id=current_user.id,
    )
    return SuccessResponse(data=None)


@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[SendMessageResponse],
    summary="Send a message to a conversation",
)
async def send_message(
    conversation_id: uuid.UUID,
    request: SendMessageRequest,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[SendMessageResponse]:
    """Process a user message and generate an assistant response."""
    assistant_msg = await service.send_message(
        conversation_id=conversation_id,
        owner_id=current_user.id,
        content=request.content,
    )
    response_dto = SendMessageResponse(
        assistant=MessageResponse.model_validate(assistant_msg)
    )
    return SuccessResponse(data=response_dto)
