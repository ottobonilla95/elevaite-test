"""
Unit tests for merge_step

Tests the merge node step that combines multiple inputs with OR or AND logic.
- first_available: Completes when ANY dependency completes (OR logic)
- wait_all: Waits for ALL dependencies to complete (AND logic)
"""

import pytest
from unittest.mock import MagicMock

from workflow_core_sdk.steps.merge_steps import merge_step
from workflow_core_sdk.execution_context import ExecutionContext, StepResult
from workflow_core_sdk.models import StepStatus


@pytest.fixture
def execution_context():
    """Create a mock execution context"""
    context = MagicMock(spec=ExecutionContext)
    context.execution_id = "test-execution-id"
    context.workflow_id = "test-workflow-id"
    context.step_io_data = {}
    context.completed_steps = set()
    context.step_results = {}
    return context


@pytest.fixture
def merge_step_config():
    """Basic merge step configuration"""
    return {
        "step_id": "merge-1",
        "step_type": "merge",
        "dependencies": ["input-1", "input-2"],
        "parameters": {"mode": "first_available", "combine_mode": "object"},
        "config": {},
    }


class TestMergeStepFirstAvailable:
    """Tests for first_available mode (OR logic)"""

    @pytest.mark.asyncio
    async def test_first_available_single_completed(self, merge_step_config, execution_context):
        """Test first_available with one dependency completed"""
        execution_context.completed_steps = {"input-1"}
        execution_context.step_results = {
            "input-1": StepResult(
                step_id="input-1",
                status=StepStatus.COMPLETED,
                output_data={"data": "from input-1"},
            )
        }

        result = await merge_step(merge_step_config, {}, execution_context)

        assert result["mode"] == "first_available"
        assert result["source_step"] == "input-1"
        assert result["data"]["data"] == "from input-1"
        assert result["completed_count"] == 1
        assert result["total_dependencies"] == 2

    @pytest.mark.asyncio
    async def test_first_available_both_completed(self, merge_step_config, execution_context):
        """Test first_available with both dependencies completed (uses first in order)"""
        execution_context.completed_steps = {"input-1", "input-2"}
        execution_context.step_results = {
            "input-1": StepResult(
                step_id="input-1",
                status=StepStatus.COMPLETED,
                output_data={"data": "from input-1"},
            ),
            "input-2": StepResult(
                step_id="input-2",
                status=StepStatus.COMPLETED,
                output_data={"data": "from input-2"},
            ),
        }

        result = await merge_step(merge_step_config, {}, execution_context)

        assert result["mode"] == "first_available"
        assert result["source_step"] == "input-1"  # First in dependency order
        assert result["completed_count"] == 2


class TestMergeStepWaitAll:
    """Tests for wait_all mode (AND logic)"""

    @pytest.mark.asyncio
    async def test_wait_all_object_combine(self, execution_context):
        """Test wait_all with object combine mode"""
        step_config = {
            "step_id": "merge-1",
            "step_type": "merge",
            "dependencies": ["input-1", "input-2"],
            "parameters": {"mode": "wait_all", "combine_mode": "object"},
        }
        execution_context.completed_steps = {"input-1", "input-2"}
        execution_context.step_results = {
            "input-1": StepResult(
                step_id="input-1",
                status=StepStatus.COMPLETED,
                output_data={"value": 1},
            ),
            "input-2": StepResult(
                step_id="input-2",
                status=StepStatus.COMPLETED,
                output_data={"value": 2},
            ),
        }

        result = await merge_step(step_config, {}, execution_context)

        assert result["mode"] == "wait_all"
        assert "input-1" in result["data"]
        assert "input-2" in result["data"]
        assert result["data"]["input-1"]["value"] == 1
        assert result["data"]["input-2"]["value"] == 2
        assert result["completed_count"] == 2

    @pytest.mark.asyncio
    async def test_wait_all_array_combine(self, execution_context):
        """Test wait_all with array combine mode"""
        step_config = {
            "step_id": "merge-1",
            "step_type": "merge",
            "dependencies": ["input-1", "input-2"],
            "parameters": {"mode": "wait_all", "combine_mode": "array"},
        }
        execution_context.completed_steps = {"input-1", "input-2"}
        execution_context.step_results = {
            "input-1": StepResult(
                step_id="input-1",
                status=StepStatus.COMPLETED,
                output_data={"value": 1},
            ),
            "input-2": StepResult(
                step_id="input-2",
                status=StepStatus.COMPLETED,
                output_data={"value": 2},
            ),
        }

        result = await merge_step(step_config, {}, execution_context)

        assert result["mode"] == "wait_all"
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2
        assert {"value": 1} in result["data"]
        assert {"value": 2} in result["data"]
