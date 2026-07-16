"""Auth API endpoints — register, login, refresh, logout, and current user."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import SuccessResponse
from app.config.settings import Settings, get_settings
from app.database.dependency import get_db_session
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[TokenResponse],
    summary="Register a new user account",
)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessResponse[TokenResponse]:
    _, access_token, refresh_token = await auth_service.register(session, request, settings)
    return SuccessResponse(
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token)
    )


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    summary="Authenticate and receive a token pair",
)
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessResponse[TokenResponse]:
    _, access_token, refresh_token = await auth_service.login(session, request, settings)
    return SuccessResponse(
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token)
    )


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    summary="Rotate the refresh token and receive a new token pair",
)
async def refresh(
    request: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SuccessResponse[TokenResponse]:
    _, access_token, refresh_token = await auth_service.refresh_tokens(
        session, request.refresh_token, settings
    )
    return SuccessResponse(
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token)
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current refresh token",
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    # FastAPI caches get_db_session per request, so this session is the same
    # one that loaded current_user — the user object is already tracked by it
    await auth_service.logout(session, current_user)


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Return the authenticated user's profile",
)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> SuccessResponse[UserResponse]:
    return SuccessResponse(data=UserResponse.model_validate(current_user))
