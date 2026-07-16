"""Workspace repository — database access for the Workspace model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspaces.models import Workspace


class WorkspaceRepository:
    """Database access object for Workspace entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, workspace: Workspace) -> Workspace:
        """Persist a new workspace and return it with server-generated fields populated."""
        self._session.add(workspace)
        await self._session.flush()
        await self._session.refresh(workspace)
        return workspace

    async def get_by_id(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Workspace | None:
        """Return the workspace only if it belongs to the given owner."""
        result = await self._session.execute(
            select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: uuid.UUID) -> list[Workspace]:
        """Return all workspaces owned by the given user, newest first."""
        result = await self._session.execute(
            select(Workspace)
            .where(Workspace.owner_id == owner_id)
            .order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_owner_and_name(
        self,
        owner_id: uuid.UUID,
        name: str,
    ) -> Workspace | None:
        """Return the workspace matching owner + name exactly (used for duplicate checks)."""
        result = await self._session.execute(
            select(Workspace).where(
                Workspace.owner_id == owner_id,
                Workspace.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, workspace: Workspace) -> Workspace:
        """Flush mutations made by the caller and return the refreshed workspace."""
        await self._session.flush()
        await self._session.refresh(workspace)
        return workspace

    async def delete(self, workspace: Workspace) -> None:
        """Delete the workspace and flush the deletion within the current transaction."""
        await self._session.delete(workspace)
        await self._session.flush()
