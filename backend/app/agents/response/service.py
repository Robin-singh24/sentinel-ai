"""Response Agent Service."""


from app.agents.response.exceptions import SentinelResponseError
from app.agents.response.models import GeneratedResponse
from app.agents.supervisor.models import WorkflowExecutionResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseService:
    """Service for generating responses from orchestrated knowledge."""
    async def generate_response(
        self,
        query: str,
        workflow_result: WorkflowExecutionResult,
    ) -> GeneratedResponse:
        """Generate a final response based on the user query and supervisor context."""
        logger.debug(
            "Generating response.",
            extra={
                "query_length": len(query),
                "chunks_count": len(workflow_result.retrieved_chunks),
            },
        )
        
        raise SentinelResponseError("Response generation is unavailable.")
