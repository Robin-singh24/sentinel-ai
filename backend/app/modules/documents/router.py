"""Document API endpoints — upload, retrieval, listing, and deletion."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import SuccessResponse
from app.config.settings import Settings, get_settings
from app.database.dependency import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.schema import DocumentResponse
from app.modules.documents.service import DocumentService
from app.modules.workspaces.repository import WorkspaceRepository
from app.storage.service import StorageService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentService:
    """Compose repositories, storage, and service for the current request session."""
    doc_repo = DocumentRepository(session)
    workspace_repo = WorkspaceRepository(session)
    storage = StorageService(settings.upload_directory)
    return DocumentService(
        doc_repo=doc_repo,
        workspace_repo=workspace_repo,
        storage=storage,
        session=session,
        max_upload_size_mb=settings.max_upload_size_mb,
    )


# ── Type aliases ──────────────────────────────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[DocumentService, Depends(get_document_service)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[DocumentResponse],
    summary="Upload a document to a workspace",
)
async def upload_document(
    workspace_id: Annotated[uuid.UUID, Form()],
    file: UploadFile,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[DocumentResponse]:
    """Upload a file to the specified workspace owned by the authenticated user."""
    document = await service.upload_document(
        workspace_id=workspace_id,
        owner_id=current_user.id,
        file=file,
    )
    return SuccessResponse(data=DocumentResponse.model_validate(document))


@router.get(
    "",
    response_model=SuccessResponse[list[DocumentResponse]],
    summary="List all documents in a workspace",
)
async def list_documents(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[list[DocumentResponse]]:
    """Return all documents belonging to the specified workspace."""
    documents = await service.list_documents(
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )
    return SuccessResponse(
        data=[DocumentResponse.model_validate(doc) for doc in documents]
    )


@router.get(
    "/{document_id}",
    response_model=SuccessResponse[DocumentResponse],
    summary="Get a document by ID",
)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> SuccessResponse[DocumentResponse]:
    """Return a single document belonging to the authenticated user's workspace."""
    document = await service.get_document(
        document_id=document_id,
        owner_id=current_user.id,
    )
    return SuccessResponse(data=DocumentResponse.model_validate(document))


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
async def delete_document(
    document_id: uuid.UUID,
    current_user: CurrentUser,
    service: Service,
) -> None:
    """Delete the document and its stored file."""
    await service.delete_document(
        document_id=document_id,
        owner_id=current_user.id,
    )
