"""
Async session factory for Sentinel AI.

`AsyncSessionFactory` is a module-level `async_sessionmaker` bound to the
application engine. It is cheap to call — each invocation produces a new
`AsyncSession` without touching the connection pool until a query is executed.

Design decisions:
  - `expire_on_commit=False`: prevents lazy-load errors after a commit when
    the session is closed. Attributes remain accessible on returned objects.
  - `autocommit=False`: all writes require an explicit commit — forces
    intentional transaction boundaries in service code.
  - `autoflush=False`: prevents implicit SQL on attribute access; makes
    execution order explicit and predictable.

Usage:
    from app.database.session import AsyncSessionFactory

    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User))
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.engine import engine

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
