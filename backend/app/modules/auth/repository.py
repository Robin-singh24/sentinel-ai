"""Auth repository — database operations for the User model."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import SentinelValidationError
from app.modules.auth.models import User


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    *,
    email: str,
    password_hash: str,
    first_name: str,
    last_name: str,
) -> User:
    user = User(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        # The unique index on `email` is the only constraint that can be violated here
        raise SentinelValidationError(
            "An account with this email already exists.", field="email"
        )
    return user


async def update_refresh_token(
    session: AsyncSession, user: User, token_hash: str | None
) -> None:
    user.refresh_token_hash = token_hash
    await session.flush()
