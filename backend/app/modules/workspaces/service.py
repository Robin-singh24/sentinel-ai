"""Workspace service — business logic and transaction management."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import SentinelNotFoundError, SentinelValidationError
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.schemas import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    """Orchestrates workspace business logic and owns all transaction boundaries."""

    def __init__(self, repository: WorkspaceRepository, session: AsyncSession) -> None:
        self._repo = repository
        self._session = session

    async def create_workspace(
        self,
        owner_id: uuid.UUID,
        data: WorkspaceCreate,
    ) -> Workspace:
        """Create a new workspace, enforcing name uniqueness per owner."""
        await self._assert_name_available(owner_id, data.name)
        workspace = Workspace(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
        )
        try:
            workspace = await self._repo.create(workspace)
            await self._session.commit()
            return workspace
        except Exception:
            await self._session.rollback()
            raise

    async def get_workspace(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Workspace:
        """Return the workspace or raise SentinelNotFoundError."""
        workspace = await self._repo.get_by_id(workspace_id, owner_id)
        if workspace is None:
            raise SentinelNotFoundError(resource="Workspace", identifier=str(workspace_id))
        return workspace

    async def list_workspaces(self, owner_id: uuid.UUID) -> list[Workspace]:
        """Return all workspaces belonging to the owner, newest first."""
        return await self._repo.get_by_owner(owner_id)

    async def update_workspace(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: WorkspaceUpdate,
    ) -> Workspace:
        """Apply partial updates to the workspace, enforcing name uniqueness if name changes."""
        workspace = await self.get_workspace(workspace_id, owner_id)

        if data.name is not None and data.name != workspace.name:
            await self._assert_name_available(owner_id, data.name)
            workspace.name = data.name

        if data.description is not None:
            workspace.description = data.description

        try:
            workspace = await self._repo.update(workspace)
            await self._session.commit()
            return workspace
        except Exception:
            await self._session.rollback()
            raise

    async def delete_workspace(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> None:
        """Delete the workspace after confirming it exists and belongs to the owner."""
        workspace = await self.get_workspace(workspace_id, owner_id)
        try:
            await self._repo.delete(workspace)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def _assert_name_available(self, owner_id: uuid.UUID, name: str) -> None:
        """Raise SentinelValidationError if the owner already has a workspace with this name."""
        existing = await self._repo.get_by_owner_and_name(owner_id, name)
        if existing is not None:
            raise SentinelValidationError(
                message=f"A workspace named '{name}' already exists.",
                field="name",
            )
