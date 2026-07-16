"""
FastAPI database session dependency for Sentinel AI.

`get_db_session` is the canonical Dependency Injection provider for obtaining
a database session inside FastAPI route handlers and sub-dependencies.

Lifecycle per request:
  1. A new `AsyncSession` is acquired from the session factory.
  2. The session is yielded to the endpoint handler.
  3. If the handler completes without raising: the session is committed.
  4. If the handler raises any exception: the session is rolled back and the
     exception is re-raised so FastAPI's exception handlers can process it.
  5. The session is always closed in the `finally` block, returning the
     underlying connection to the pool regardless of outcome.

Usage:
    from typing import Annotated
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database.dependency import get_db_session

    async def my_route(
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> ...:
        result = await db.execute(select(MyModel))
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionFactory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a scoped `AsyncSession` for the duration of a single request.

    The session is committed on success and rolled back on any exception.
    Connection is always returned to the pool when the request completes.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
