"""
SQLAlchemy Declarative Base for Sentinel AI.

All ORM models across every domain module must inherit from `Base` defined
here. This guarantees a single, unified `MetaData` object, which is required
for Alembic's `--autogenerate` to discover all tables in one sweep.

Usage:
    from app.database.base import Base

    class User(Base):
        __tablename__ = "users"
        ...

Do NOT create a separate DeclarativeBase in any other module.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared declarative base class for all Sentinel AI ORM models.

    Inheriting from SQLAlchemy's `DeclarativeBase` (2.x style) gives each
    subclass:
      - A mapped `__tablename__` attribute.
      - Full SQLAlchemy 2.x typed-column support.
      - Registration in `Base.metadata` for Alembic autogenerate.
    """
