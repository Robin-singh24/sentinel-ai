"""Document repository — database access for the Document model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document, DocumentStatus
from app.modules.workspaces.models import Workspace


class DocumentRepository:
    """Database access object for Document entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, document: Document) -> Document:
        """Persist a new document and return it with server-generated fields populated."""
        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def get_by_id(
        self,
        document_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Document | None:
        """Return the document only if its parent workspace belongs to the given user."""
        result = await self._session.execute(
            select(Document)
            .join(Workspace, Document.workspace_id == Workspace.id)
            .where(
                Document.id == document_id,
                Workspace.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> list[Document]:
        """Return all documents in the workspace, newest first, verified by owner."""
        result = await self._session.execute(
            select(Document)
            .join(Workspace, Document.workspace_id == Workspace.id)
            .where(
                Document.workspace_id == workspace_id,
                Workspace.owner_id == owner_id,
            )
            .order_by(Document.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, document: Document) -> None:
        """Delete the document and flush the deletion within the current transaction."""
        await self._session.delete(document)
        await self._session.flush()

    async def update_status(
        self,
        document: Document,
        status: DocumentStatus,
    ) -> Document:
        """Apply a status transition and flush the update within the current transaction."""
        document.status = status
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def get_by_checksum(
        self,
        workspace_id: uuid.UUID,
        checksum: str,
    ) -> Document | None:
        """Return the document matching the checksum within the given workspace."""
        result = await self._session.execute(
            select(Document).where(
                Document.workspace_id == workspace_id,
                Document.checksum == checksum,
            )
        )
        return result.scalar_one_or_none()
