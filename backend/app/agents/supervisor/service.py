"""Supervisor service — AI agent orchestration and workflow coordination."""

from app.agents.supervisor.classifier import IntentClassifier
from app.agents.supervisor.exceptions import SentinelSupervisorError
from app.agents.supervisor.models import WorkflowExecutionResult, WorkflowType
from app.agents.supervisor.planner import WorkflowPlanner
from app.common.exceptions import SentinelBaseException
from app.config.settings import Settings
from app.core.logging import get_logger
from app.llms.embeddings.orchestrator import EmbeddingOrchestrator
from app.modules.retrieval.service import RetrievalService
from app.vectorstore.repositories.models import VectorSearchParams

logger = get_logger(__name__)


class SupervisorService:
    """Supervisor service for AI agent orchestration."""

    def __init__(
        self,
        intent_classifier: IntentClassifier,
        workflow_planner: WorkflowPlanner,
        embedding_orchestrator: EmbeddingOrchestrator,
        retrieval_service: RetrievalService,
        settings: Settings,
    ) -> None:
        self._intent_classifier = intent_classifier
        self._workflow_planner = workflow_planner
        self._embedding_orchestrator = embedding_orchestrator
        self._retrieval_service = retrieval_service
        self._settings = settings

    async def process_query(
        self,
        query: str,
        limit: int = 5,
    ) -> WorkflowExecutionResult:
        """Process a user query through the complete AI workflow."""

        logger.info(
            "Processing user query.",
            extra={"query_length": len(query), "limit": limit},
        )

        try:
            # Step 1: Classify user intent
            intent = self._intent_classifier.classify(query)
            logger.debug(f"Classified intent: {intent.intent}")

            # Step 2: Create workflow plan
            plan = self._workflow_planner.plan(intent)
            logger.debug(f"Created workflow plan: {plan.workflow}")

            # Step 3: Execute workflow
            if plan.workflow == WorkflowType.RETRIEVAL:
                result = await self._execute_retrieval_workflow(query, limit)
            else:
                raise SentinelSupervisorError(
                    f"Unsupported workflow type: {plan.workflow}. "
                    "No execution handler exists for this workflow."
                )

            logger.info(
                "Query processing completed.",
                extra={
                    "workflow": plan.workflow.value,
                    "results_count": len(result.retrieved_chunks),
                },
            )

            return result
        except SentinelBaseException:
            raise
        except Exception as e:
            logger.error("Unexpected orchestration failure.", extra={"error": str(e)})
            raise SentinelSupervisorError(f"Unexpected orchestration failure: {str(e)}") from e

    async def _execute_retrieval_workflow(
        self,
        query: str,
        limit: int,
    ) -> WorkflowExecutionResult:
        """Execute the knowledge retrieval workflow."""
        # Step 1: Generate query embedding
        query_vector = self._embedding_orchestrator.embed_query(query)
        logger.debug(f"Generated query embedding with dimension {len(query_vector)}")

        # Step 2: Build retrieval parameters
        # Collection name is an internal implementation detail
        collection_name = "documents"
        
        search_params = VectorSearchParams(
            collection_name=collection_name,
            vector=query_vector,
            limit=limit,
        )

        # Step 3: Execute retrieval
        retrieved_chunks = await self._retrieval_service.retrieve(search_params)
        
        logger.debug(f"Retrieved {len(retrieved_chunks)} chunks from collection '{collection_name}'")

        # Step 4: Wrap results
        return WorkflowExecutionResult(retrieved_chunks=retrieved_chunks)
