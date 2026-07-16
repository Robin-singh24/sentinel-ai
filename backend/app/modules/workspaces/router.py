"""Workspace API endpoints — CRUD operations for the workspace domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import SuccessResponse
from app.database.dependency import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.schemas import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


def get_workspace_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkspaceService:
    """Compose the repository and service for the current request session."""
    repository = WorkspaceRepository(session)
    return WorkspaceService(repository=repository, session=session)


# ── Type aliases ──────────────────────────────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[WorkspaceService, Depends(get_workspace_service)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[WorkspaceResponse],
    summary="Create a new workspace",
)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[WorkspaceResponse]:
    """Create a workspace owned by the authenticated user."""
    workspace = await service.create_workspace(owner_id=current_user.id, data=data)
    return SuccessResponse(data=WorkspaceResponse.model_validate(workspace))


@router.get(
    "",
    response_model=SuccessResponse[list[WorkspaceResponse]],
    summary="List all workspaces for the authenticated user",
)
async def list_workspaces(
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[list[WorkspaceResponse]]:
    """Return all workspaces owned by the authenticated user, newest first."""
    workspaces = await service.list_workspaces(owner_id=current_user.id)
    return SuccessResponse(
        data=[WorkspaceResponse.model_validate(ws) for ws in workspaces]
    )


@router.get(
    "/{workspace_id}",
    response_model=SuccessResponse[WorkspaceResponse],
    summary="Get a workspace by ID",
)
async def get_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[WorkspaceResponse]:
    """Return a single workspace belonging to the authenticated user."""
    workspace = await service.get_workspace(
        workspace_id=workspace_id, owner_id=current_user.id
    )
    return SuccessResponse(data=WorkspaceResponse.model_validate(workspace))


@router.put(
    "/{workspace_id}",
    response_model=SuccessResponse[WorkspaceResponse],
    summary="Update a workspace",
)
async def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[WorkspaceResponse]:
    """Apply partial updates to the workspace owned by the authenticated user."""
    workspace = await service.update_workspace(
        workspace_id=workspace_id, owner_id=current_user.id, data=data
    )
    return SuccessResponse(data=WorkspaceResponse.model_validate(workspace))


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace",
)
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> None:
    """Delete the workspace owned by the authenticated user."""
    await service.delete_workspace(
        workspace_id=workspace_id, owner_id=current_user.id
    )
