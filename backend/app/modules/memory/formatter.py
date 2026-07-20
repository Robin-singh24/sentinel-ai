"""Memory Formatter for transforming domain memory into prompt-ready strings."""

from dataclasses import dataclass

from app.core.logging import get_logger
from app.modules.memory.models import ConversationMemory

logger = get_logger(__name__)


@dataclass(frozen=True)
class FormattedMemory:
    """Immutable encapsulation of the formatted memory block."""
    memory: str


class MemoryFormatter:
    """Transforms conversation memory into a deterministic formatted string."""

    def format(self, memory: ConversationMemory) -> FormattedMemory:
        """Formats each message according to its role and chronological order."""
        if not memory.messages:
            logger.debug("Formatting empty conversation memory.")
            return FormattedMemory(memory="")
            
        logger.debug(
            "Formatting conversation memory.",
            extra={"message_count": len(memory.messages)}
        )
        
        formatted_blocks = []
        for message in memory.messages:
            # Prefix role with capitalized first letter
            role = message.role.value.capitalize()
            # Construct standard formatted block
            block = f"{role}: {message.content.strip()}"
            formatted_blocks.append(block)
            
        # Join with double newlines for readability
        final_memory_string = "\n\n".join(formatted_blocks)
        
        return FormattedMemory(memory=final_memory_string)
