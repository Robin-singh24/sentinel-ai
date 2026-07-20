"""Unit tests for the Prompt Builder."""

from app.agents.response.dependencies import get_prompt_builder
from app.agents.response.models import FormattedContext, Prompt
from app.agents.response.prompt_builder import PromptBuilder
from app.agents.response.prompt_templates import SYSTEM_PROMPT


class TestPromptBuilder:
    """Tests for the PromptBuilder logic."""

    def test_build_constructs_valid_prompt(self):
        """Verify that the builder correctly injects context and query into the templates."""
        builder = PromptBuilder()
        
        query = "What is the capital of France?"
        context_text = "[Context 1]\nParis is the capital of France."
        context = FormattedContext(text=context_text)
        
        result = builder.build(query=query, context=context)
        
        assert isinstance(result, Prompt)
        
        # System prompt should match the template exactly
        assert result.system_prompt == SYSTEM_PROMPT
        
        # User prompt should contain the query and context
        assert query in result.user_prompt
        assert context_text in result.user_prompt
        
        # Ensure it's not just a blind concatenation
        assert "--- CONTEXT ---" in result.user_prompt
        assert "--- QUERY ---" in result.user_prompt

    def test_build_handles_empty_context(self):
        """Verify behavior when the context is empty."""
        builder = PromptBuilder()
        
        query = "Tell me something."
        context = FormattedContext(text="")
        
        result = builder.build(query=query, context=context)
        
        assert isinstance(result, Prompt)
        assert query in result.user_prompt
        # The context block will just be empty between the delimiters
        assert "--- CONTEXT ---\n\n--- END CONTEXT ---" in result.user_prompt


class TestPromptDependencies:
    """Test prompt builder dependency injection."""
    
    def test_get_prompt_builder(self):
        """Verify factory returns correct instance."""
        builder = get_prompt_builder()
        assert isinstance(builder, PromptBuilder)
