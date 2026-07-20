from collections.abc import AsyncGenerator

import pytest_asyncio
from app.config.settings import get_settings
from app.database.base import Base
import app.database.models  # noqa: F401 (Ensure models are registered)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Provides a PostgreSQL engine connected to the test database."""
    settings = get_settings()
    
    # We force localhost for tests running on the host OS
    test_url = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@localhost:{settings.postgres_port}/sentinel_test"
    )
    
    engine = create_async_engine(
        test_url,
        echo=False,
        pool_pre_ping=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provides a fresh transactional session for each test."""
    # Create a sessionmaker specifically for this engine
    session_factory = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with session_factory() as session:
        yield session
        # Rollback any uncommitted changes after each test to keep DB clean
        await session.rollback()
