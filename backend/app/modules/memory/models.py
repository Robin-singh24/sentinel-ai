"""Domain models for the Conversation Memory subsystem."""

import enum
from dataclasses import dataclass


class MemoryRole(enum.StrEnum):
    """Identifies the author of a message in memory."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class MemoryMessage:
    """Represents a single message turn in memory."""
    role: MemoryRole
    content: str


@dataclass(frozen=True)
class ConversationMemory:
    """Provider-agnostic memory model. Messages are ordered chronologically (oldest → newest)."""
    messages: list[MemoryMessage]
