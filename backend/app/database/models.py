"""Registers all ORM models with SQLAlchemy."""

from app.modules.auth.models import User
from app.modules.conversations.models import Conversation, Message
from app.modules.documents.models import Document
from app.modules.workspaces.models import Workspace

__all__ = [
    "User",
    "Workspace",
    "Document",
    "Conversation",
    "Message",
]