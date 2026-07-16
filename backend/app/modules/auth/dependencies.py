"""FastAPI dependency for authenticated endpoints."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.database.dependency import get_db_session
from app.modules.auth import service as auth_service
from app.modules.auth.models import User

_bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Extract and validate the Bearer JWT, returning the authenticated User.

    FastAPI raises HTTP 403 automatically when no Authorization header is present,
    so this function only needs to handle token validation failures.
    """
    return await auth_service.get_current_user(session, credentials.credentials, settings)
