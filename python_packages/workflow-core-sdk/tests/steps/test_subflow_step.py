"""
Unit tests for subflow_step

Tests subflow execution with input/output mapping and context inheritance.
"""

import pytest
from unittest.mock import MagicMock

from workflow_core_sdk.steps.flow_steps import subflow_step
from workflow_core_sdk.execution_context import ExecutionContext, ExecutionStatus, UserContext


@pytest.fixture
def user_context():
    """Create a mock user context"""
    return UserContext(
        user_id="test-user",
        session_id="test-session",
        organization_id="test-org",
    )


@pytest.fixture
def execution_context(user_context):
    """Create a mock execution context"""
    context = MagicMock(spec=ExecutionContext)
    context.execution_id = "parent-execution-id"
    context.workflow_id = "parent-workflow-id"
    context.user_context = user_context
    context.workflow_engine = MagicMock()
    context.step_io_data = {}
    context.status = ExecutionStatus.RUNNING
    return context


class TestSubflowConfiguration:
    """Tests for subflow configuration validation"""

    @pytest.mark.asyncio
    async def test_missing_workflow_id(self, execution_context):
        """Test error when workflow_id is missing"""
        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {},
        }

        result = await subflow_step(config, {}, execution_context)

        assert result["success"] is False
        assert "workflow_id" in result["error"]
        assert result["subflow_id"] is None
