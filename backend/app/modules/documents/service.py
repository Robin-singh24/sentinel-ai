"""Document service — business logic and transaction management."""

import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import SentinelNotFoundError, SentinelValidationError
from app.modules.documents.models import Document, DocumentStatus
from app.modules.documents.repository import DocumentRepository
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.repository import WorkspaceRepository
from app.storage.service import StorageService


class DocumentService:
    """Orchestrates document upload, retrieval, listing, and deletion.

    Coordinates the document repository and storage service while keeping
    each layer unaware of the other. Owns all transaction boundaries.
    """

    def __init__(
        self,
        doc_repo: DocumentRepository,
        workspace_repo: WorkspaceRepository,
        storage: StorageService,
        session: AsyncSession,
        max_upload_size_mb: int = 25,
    ) -> None:
        self._doc_repo = doc_repo
        self._workspace_repo = workspace_repo
        self._storage = storage
        self._session = session
        self._max_upload_size_bytes = max_upload_size_mb * 1024 * 1024

    async def upload_document(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
        file: UploadFile,
    ) -> Document:
        """Validate, store, and persist a new document.

        Guarantees atomicity: if the database write fails after the file is
        saved, the file is removed to prevent storage/DB divergence.
        """
        workspace = await self._get_workspace(workspace_id, owner_id)

        # Read once — UploadFile is a stream and cannot be re-read without seeking
        file_data = await file.read()

        # Enforce size limit after reading; avoids a separate partial-read pass
        if len(file_data) > self._max_upload_size_bytes:
            raise SentinelValidationError(
                message=(
                    f"File size {len(file_data)} bytes exceeds the maximum allowed "
                    f"{self._max_upload_size_bytes} bytes."
                ),
                field="file",
            )

        checksum = self._storage.generate_checksum(file_data)

        await self._assert_no_duplicate(workspace.id, checksum)

        storage_path: str | None = None
        try:
            storage_path = self._storage.save_file(
                file_data=file_data,
                workspace_id=workspace.id,
                original_filename=file.filename or "upload",
            )
            document = Document(
                workspace_id=workspace.id,
                uploaded_by=owner_id,
                filename=storage_path.split("/")[-1],
                original_filename=file.filename or "upload",
                mime_type=file.content_type or "application/octet-stream",
                file_size=len(file_data),
                storage_path=storage_path,
                status=DocumentStatus.uploaded,
                checksum=checksum,
            )
            document = await self._doc_repo.create(document)
            await self._session.commit()
            return document
        except Exception:
            await self._session.rollback()
            # Remove the written file if the DB transaction failed
            if storage_path and self._storage.file_exists(storage_path):
                self._storage.delete_file(storage_path)
            raise

    async def get_document(
        self,
        document_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Document:
        """Return the document or raise SentinelNotFoundError."""
        document = await self._doc_repo.get_by_id(document_id, owner_id)
        if document is None:
            raise SentinelNotFoundError(resource="Document", identifier=str(document_id))
        return document

    async def list_documents(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> list[Document]:
        """Return all documents in the workspace after verifying ownership."""
        await self._get_workspace(workspace_id, owner_id)
        return await self._doc_repo.list_by_workspace(workspace_id, owner_id)

    async def delete_document(
        self,
        document_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> None:
        """Delete the stored file and the database record atomically."""
        document = await self.get_document(document_id, owner_id)
        try:
            # Delete file first; if DB delete fails, the file is already gone
            # an acceptable trade-off since orphaned DB rows are easier to reconcile
            # than orphaned files consuming unbounded disk space.
            self._storage.delete_file(document.storage_path)
            await self._doc_repo.delete(document)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def _get_workspace(
        self,
        workspace_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Workspace:
        """Return the workspace or raise SentinelNotFoundError."""
        workspace = await self._workspace_repo.get_by_id(workspace_id, owner_id)
        if workspace is None:
            raise SentinelNotFoundError(resource="Workspace", identifier=str(workspace_id))
        return workspace

    async def _assert_no_duplicate(
        self,
        workspace_id: uuid.UUID,
        checksum: str,
    ) -> None:
        """Raise SentinelValidationError if an identical file already exists in the workspace."""
        existing = await self._doc_repo.get_by_checksum(workspace_id, checksum)
        if existing is not None:
            raise SentinelValidationError(
                message="An identical file already exists in this workspace.",
                field="file",
            )
