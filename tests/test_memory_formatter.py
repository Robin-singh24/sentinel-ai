"""Unit tests for the Memory Formatter."""

from app.modules.memory.formatter import FormattedMemory, MemoryFormatter
from app.modules.memory.models import ConversationMemory, MemoryMessage, MemoryRole


class TestMemoryFormatter:
    """Tests for the MemoryFormatter component."""

    def test_format_empty_memory(self):
        """Verify empty memory returns an empty formatted block."""
        formatter = MemoryFormatter()
        memory = ConversationMemory(messages=[])
        
        result = formatter.format(memory)
        
        assert isinstance(result, FormattedMemory)
        assert result.memory == ""

    def test_format_preserves_order_and_roles(self):
        """Verify the formatter preserves chronological ordering and capitalizes roles."""
        formatter = MemoryFormatter()
        memory = ConversationMemory(
            messages=[
                MemoryMessage(role=MemoryRole.SYSTEM, content="You are helpful."),
                MemoryMessage(role=MemoryRole.USER, content="Hello!"),
                MemoryMessage(role=MemoryRole.ASSISTANT, content="Hi there!"),
            ]
        )
        
        result = formatter.format(memory)
        
        expected_memory = (
            "System: You are helpful.\n\n"
            "User: Hello!\n\n"
            "Assistant: Hi there!"
        )
        
        assert isinstance(result, FormattedMemory)
        assert result.memory == expected_memory

    def test_format_strips_whitespace(self):
        """Verify the formatter trims whitespace from message contents."""
        formatter = MemoryFormatter()
        memory = ConversationMemory(
            messages=[
                MemoryMessage(role=MemoryRole.USER, content="  Spaced out. \n"),
            ]
        )
        
        result = formatter.format(memory)
        
        assert result.memory == "User: Spaced out."
