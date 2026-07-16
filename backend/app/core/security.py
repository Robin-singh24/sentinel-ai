"""
Pure security utilities — password hashing and JWT operations.

All functions are stateless and carry no framework or database dependencies
so they can be tested in isolation and called from any layer.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.common.exceptions import SentinelUnauthorizedError
from app.config.settings import Settings

_password_hasher = PasswordHash([Argon2Hasher()])


def hash_password(plain: str) -> str:
    """Return an Argon2 hash of the plaintext password."""
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored Argon2 hash."""
    return _password_hasher.verify(plain, hashed)


def hash_token(token: str) -> str:
    """SHA-256 the token string before persisting it.

    Refresh tokens are high-entropy random values so SHA-256 is sufficient;
    Argon2 would add unnecessary latency on every refresh request.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    """Issue a short-lived JWT access token."""
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID, settings: Settings) -> str:
    """Issue a long-lived JWT refresh token."""
    expire = datetime.now(tz=timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str, settings: Settings) -> dict:
    """Decode and validate a JWT, returning its payload.

    `expected_type` prevents access tokens from being accepted where a refresh
    token is required and vice versa.
    """
    try:
        payload: dict = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except InvalidTokenError:
        raise SentinelUnauthorizedError("Invalid or expired token.")

    if payload.get("type") != expected_type:
        raise SentinelUnauthorizedError("Invalid token type.")

    return payload
