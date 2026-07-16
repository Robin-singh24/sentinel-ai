"""Auth service — business logic for registration, login, token lifecycle."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import SentinelUnauthorizedError
from app.config.settings import Settings
from app.core import security
from app.modules.auth import repository
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RegisterRequest


async def register(
    session: AsyncSession,
    request: RegisterRequest,
    settings: Settings,
) -> tuple[User, str, str]:
    """Create a new account and return (user, access_token, refresh_token)."""
    password_hash = security.hash_password(request.password)
    user = await repository.create(
        session,
        email=request.email,
        password_hash=password_hash,
        first_name=request.first_name,
        last_name=request.last_name,
    )
    access_token, refresh_token = _issue_token_pair(user.id, settings)
    await repository.update_refresh_token(session, user, security.hash_token(refresh_token))
    return user, access_token, refresh_token


async def login(
    session: AsyncSession,
    request: LoginRequest,
    settings: Settings,
) -> tuple[User, str, str]:
    """Verify credentials and return (user, access_token, refresh_token)."""
    user = await repository.get_by_email(session, request.email)
    if not user or not security.verify_password(request.password, user.password_hash):
        # Deliberate vagueness — don't reveal whether the email is registered
        raise SentinelUnauthorizedError("Invalid email or password.")
    if not user.is_active:
        raise SentinelUnauthorizedError("This account has been deactivated.")
    access_token, refresh_token = _issue_token_pair(user.id, settings)
    await repository.update_refresh_token(session, user, security.hash_token(refresh_token))
    return user, access_token, refresh_token


async def refresh_tokens(
    session: AsyncSession,
    refresh_token: str,
    settings: Settings,
) -> tuple[User, str, str]:
    """Rotate the refresh token and return (user, new_access_token, new_refresh_token)."""
    payload = security.decode_token(refresh_token, expected_type="refresh", settings=settings)
    user_id = uuid.UUID(payload["sub"])
    user = await repository.get_by_id(session, user_id)

    stored_hash = user.refresh_token_hash if user else None
    if stored_hash is None or stored_hash != security.hash_token(refresh_token):
        # Hash mismatch means the token was already rotated or the user logged out;
        # treat as a potential replay attack and reject
        raise SentinelUnauthorizedError("Refresh token is invalid or has already been used.")

    access_token, new_refresh_token = _issue_token_pair(user.id, settings)
    await repository.update_refresh_token(session, user, security.hash_token(new_refresh_token))
    return user, access_token, new_refresh_token


async def logout(session: AsyncSession, user: User) -> None:
    """Revoke the refresh token, preventing further token rotation."""
    await repository.update_refresh_token(session, user, None)


async def get_current_user(
    session: AsyncSession,
    token: str,
    settings: Settings,
) -> User:
    """Decode an access token and return the corresponding active User."""
    payload = security.decode_token(token, expected_type="access", settings=settings)
    user_id = uuid.UUID(payload["sub"])
    user = await repository.get_by_id(session, user_id)
    if not user or not user.is_active:
        raise SentinelUnauthorizedError("User not found or deactivated.")
    return user


def _issue_token_pair(user_id: uuid.UUID, settings: Settings) -> tuple[str, str]:
    access_token = security.create_access_token(user_id, settings)
    refresh_token = security.create_refresh_token(user_id, settings)
    return access_token, refresh_token
