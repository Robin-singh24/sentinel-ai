"""Workspace model — an isolated knowledge environment owned by a single user."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.modules.auth.models import User
    from app.modules.conversations.models import Conversation
    from app.modules.documents.models import Document


class Workspace(Base):
    """Represents an isolated knowledge environment owned by a single user."""

    __tablename__ = "workspaces"

    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "name",
            name="uq_workspace_owner_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # RESTRICT prevents silent data loss if a user is deleted while owning workspaces
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship("User", back_populates="workspaces")
    documents: Mapped[list[Document]] = relationship(
        "Document", back_populates="workspace", passive_deletes=True
    )
    conversations: Mapped[list[Conversation]] = relationship(
        "Conversation", back_populates="workspace", passive_deletes=True
    )
