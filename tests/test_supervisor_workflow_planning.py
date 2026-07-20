"""Workflow planning tests for the supervisor module.

These tests validate the workflow planner's ability to create execution plans
based on classified intents.
"""

import pytest

from app.agents.supervisor.dependencies import get_workflow_planner
from app.agents.supervisor.exceptions import SentinelSupervisorError
from app.agents.supervisor.models import ClassifiedIntent, IntentType, WorkflowPlan, WorkflowType
from app.agents.supervisor.planner import WorkflowPlanner


class TestWorkflowPlanner:
    """Test the WorkflowPlanner logic."""

    def test_knowledge_retrieval_intent_creates_retrieval_plan(self):
        """Test that KNOWLEDGE_RETRIEVAL intent maps to RETRIEVAL workflow."""
        planner = WorkflowPlanner()
        intent = ClassifiedIntent(intent=IntentType.KNOWLEDGE_RETRIEVAL)
        
        plan = planner.plan(intent)
        
        assert isinstance(plan, WorkflowPlan)
        assert plan.workflow == WorkflowType.RETRIEVAL

    def test_unknown_intent_raises_error(self):
        """Test that UNKNOWN intent raises SentinelSupervisorError."""
        planner = WorkflowPlanner()
        intent = ClassifiedIntent(intent=IntentType.UNKNOWN)
        
        with pytest.raises(SentinelSupervisorError) as exc_info:
            planner.plan(intent)
        
        error = exc_info.value
        assert "UNKNOWN intent" in error.message
        assert error.code == "SUPERVISOR_ERROR"

    def test_workflow_plan_is_frozen(self):
        """Test that WorkflowPlan is immutable."""
        planner = WorkflowPlanner()
        intent = ClassifiedIntent(intent=IntentType.KNOWLEDGE_RETRIEVAL)
        plan = planner.plan(intent)
        
        with pytest.raises(AttributeError):
            plan.workflow = WorkflowType.RETRIEVAL  # type: ignore

    def test_planner_is_stateless(self):
        """Test that planner produces consistent results (stateless behavior)."""
        planner = WorkflowPlanner()
        intent = ClassifiedIntent(intent=IntentType.KNOWLEDGE_RETRIEVAL)
        
        plan1 = planner.plan(intent)
        plan2 = planner.plan(intent)
        
        assert plan1.workflow == plan2.workflow
        # Plans are frozen dataclasses, so they should be equal
        assert plan1 == plan2


class TestWorkflowPlannerDependencyInjection:
    """Test the workflow planner dependency injection."""

    def test_get_workflow_planner_returns_instance(self):
        """Test that get_workflow_planner returns a WorkflowPlanner instance."""
        planner = get_workflow_planner()
        assert isinstance(planner, WorkflowPlanner)

    def test_get_workflow_planner_creates_new_instance(self):
        """Test that get_workflow_planner creates a new instance each time."""
        planner1 = get_workflow_planner()
        planner2 = get_workflow_planner()
        assert planner1 is not planner2

    def test_planner_from_di_works_correctly(self):
        """Test that planner obtained via DI works as expected."""
        planner = get_workflow_planner()
        intent = ClassifiedIntent(intent=IntentType.KNOWLEDGE_RETRIEVAL)
        plan = planner.plan(intent)
        assert plan.workflow == WorkflowType.RETRIEVAL
