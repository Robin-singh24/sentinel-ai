"""FastAPI dependency injection for the retrieval service."""

from typing import Annotated

from fastapi import Depends

from app.modules.retrieval.service import RetrievalService
from app.vectorstore.dependencies import get_vector_repository
from app.vectorstore.repositories.repository import VectorRepository


def get_retrieval_service(
    vector_repo: Annotated[VectorRepository, Depends(get_vector_repository)],
) -> RetrievalService:
    """Compose and return a RetrievalService with injected dependencies.

    Args:
        vector_repo: Injected VectorRepository for vector operations.

    Returns:
        Fully initialized RetrievalService instance.
    """
    return RetrievalService(vector_repository=vector_repo)
