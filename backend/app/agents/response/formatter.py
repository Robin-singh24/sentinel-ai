"""Context Formatter for the Response Agent."""

from app.agents.response.models import FormattedContext
from app.agents.supervisor.models import WorkflowExecutionResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContextFormatter:
    """Transforms orchestrated knowledge into a deterministic context representation."""

    def format(self, workflow_result: WorkflowExecutionResult) -> FormattedContext:
        """Transforms orchestrated knowledge into a deterministic context representation."""
        logger.debug(
            "Formatting context from workflow execution result.",
            extra={"chunks_count": len(workflow_result.retrieved_chunks)}
        )
        
        formatted_blocks = []
        for i, chunk in enumerate(workflow_result.retrieved_chunks, start=1):
            # We assume the textual content is stored in a 'text' or 'content' field in the payload.
            # Fallback to string representation of the payload if specific text field is absent.
            if not chunk.payload:
                continue
                
            text_content = chunk.payload.get("text") or chunk.payload.get("content")
            if not text_content:
                text_content = str(chunk.payload)
                
            block = f"[Context {i}]\n{text_content.strip()}"
            formatted_blocks.append(block)
            
        final_text = "\n\n".join(formatted_blocks)
        return FormattedContext(text=final_text)
