"""
Unit tests for ExecutionContext

Tests execution context initialization, state management, and data flow.
"""

import pytest
from workflow_core_sdk.execution_context import (
    ExecutionContext,
    StepResult,
    UserContext,
)
from workflow_core_sdk.models import ExecutionStatus, StepStatus


@pytest.fixture
def basic_workflow_config():
    """Create a basic workflow configuration"""
    return {
        "workflow_id": "test-workflow-123",
        "name": "Test Workflow",
        "steps": [
            {
                "step_id": "step1",
                "step_type": "data_input",
                "name": "Input Step",
            },
            {
                "step_id": "step2",
                "step_type": "data_processing",
                "name": "Processing Step",
                "dependencies": ["step1"],
                "input_mapping": {"data": "step1.output"},
            },
            {
                "step_id": "step3",
                "step_type": "data_output",
                "name": "Output Step",
                "dependencies": ["step2"],
                "input_mapping": {"result": "step2.processed"},
            },
        ],
    }


@pytest.fixture
def user_context():
    """Create a user context"""
    return UserContext(
        user_id="user-123",
        session_id="session-456",
        organization_id="org-789",
        permissions=["read", "write"],
    )


class TestExecutionContextInitialization:
    """Tests for ExecutionContext initialization"""

    def test_basic_initialization(self, basic_workflow_config):
        """Test basic context initialization"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        assert context.workflow_id == "test-workflow-123"
        assert context.workflow_name == "Test Workflow"
        assert context.status == ExecutionStatus.PENDING
        assert context.execution_id is not None
        assert len(context.steps_config) == 3

    def test_initialization_with_user_context(self, basic_workflow_config, user_context):
        """Test initialization with user context"""
        context = ExecutionContext(workflow_config=basic_workflow_config, user_context=user_context)

        assert context.user_context.user_id == "user-123"
        assert context.user_context.organization_id == "org-789"
        assert "read" in context.user_context.permissions

    def test_initialization_with_custom_execution_id(self, basic_workflow_config):
        """Test initialization with custom execution ID"""
        custom_id = "custom-exec-123"
        context = ExecutionContext(workflow_config=basic_workflow_config, execution_id=custom_id)

        assert context.execution_id == custom_id

    def test_analytics_ids_initialization(self, basic_workflow_config):
        """Test analytics IDs are properly initialized"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        assert context.analytics_ids is not None
        assert context.analytics_ids.execution_id == context.execution_id


class TestStepNormalization:
    """Tests for step normalization"""

    def test_normalize_steps_with_missing_step_ids(self):
        """Test normalization adds step_ids when missing"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test",
            "steps": [
                {"step_type": "trigger", "name": "Trigger"},
                {"step_type": "data_input", "name": "Input Step"},
                {"step_type": "data_processing", "name": "Process Data"},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)

        # Trigger should get 'trigger' as step_id
        assert context.steps_config[0].step_id == "trigger"
        # Others should get slugified names
        assert context.steps_config[1].step_id == "input_step"
        assert context.steps_config[2].step_id == "process_data"

    def test_normalize_steps_with_duplicate_names(self):
        """Test normalization handles duplicate names"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test",
            "steps": [
                {"step_type": "data_input", "name": "Input"},
                {"step_type": "data_input", "name": "Input"},
                {"step_type": "data_input", "name": "Input"},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)

        # Should have unique step_ids
        step_ids = [step.step_id for step in context.steps_config]
        assert len(step_ids) == len(set(step_ids))  # All unique
        assert "input" in step_ids
        assert "input_2" in step_ids
        assert "input_3" in step_ids


class TestExecutionStateManagement:
    """Tests for execution state management"""

    def test_start_execution(self, basic_workflow_config):
        """Test starting execution"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        assert context.status == ExecutionStatus.PENDING
        assert context.started_at is None

        context.start_execution()

        assert context.status == ExecutionStatus.RUNNING
        assert context.started_at is not None
        assert "started_at" in context.metadata

    def test_complete_execution(self, basic_workflow_config):
        """Test completing execution"""
        context = ExecutionContext(workflow_config=basic_workflow_config)
        context.start_execution()

        context.complete_execution()

        assert context.status == ExecutionStatus.COMPLETED
        assert context.completed_at is not None
        assert "completed_at" in context.metadata
        assert "duration_ms" in context.metadata

    def test_fail_execution(self, basic_workflow_config):
        """Test failing execution"""
        context = ExecutionContext(workflow_config=basic_workflow_config)
        context.start_execution()

        error_message = "Test error"
        context.fail_execution(error_message)

        assert context.status == ExecutionStatus.FAILED
        assert context.completed_at is not None
        assert context.metadata["error_message"] == error_message
        assert "duration_ms" in context.metadata


class TestStepManagement:
    """Tests for step management"""

    def test_get_step_config(self, basic_workflow_config):
        """Test getting step configuration"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        step_config = context.get_step_config("step1")
        assert step_config is not None
        assert step_config.step_id == "step1"
        assert step_config.step_type == "data_input"

    def test_get_step_config_not_found(self, basic_workflow_config):
        """Test getting non-existent step configuration"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        step_config = context.get_step_config("nonexistent")
        assert step_config is None

    def test_store_step_result(self, basic_workflow_config):
        """Test storing step result"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        result = StepResult(
            step_id="step1",
            status=StepStatus.COMPLETED,
            output_data={"result": "success"},
        )

        context.store_step_result(result)

        assert "step1" in context.step_results
        assert context.step_results["step1"] == result
        assert "step1" in context.completed_steps
        assert "step1" not in context.pending_steps


class TestDataFlow:
    """Tests for data flow between steps"""

    def test_get_step_input_data_with_mapping(self, basic_workflow_config):
        """Test getting step input data with mapping"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        # Store output from step1
        context.step_io_data["step1"] = {"output": "test data"}

        # Get input for step2 (which maps from step1.output)
        input_data = context.get_step_input_data("step2")

        assert "data" in input_data
        assert input_data["data"] == "test data"

    def test_get_step_input_data_with_direct_reference(self):
        """Test getting step input data with direct step reference"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {
                    "step_id": "step2",
                    "step_type": "data_processing",
                    "input_mapping": {"input": "step1"},
                },
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        context.step_io_data["step1"] = {"result": "data"}

        input_data = context.get_step_input_data("step2")

        assert "input" in input_data
        assert input_data["input"] == {"result": "data"}

    def test_get_step_input_data_with_global_variables(self):
        """Test getting step input data from global variables"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {
                    "step_id": "step1",
                    "step_type": "data_input",
                    "input_mapping": {"config": "api_key"},
                }
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        context.global_variables["api_key"] = "secret-key-123"

        input_data = context.get_step_input_data("step1")

        assert "config" in input_data
        assert input_data["config"] == "secret-key-123"


class TestDependencyGraph:
    """Tests for dependency graph building"""

    def test_build_dependency_graph(self, basic_workflow_config):
        """Test dependency graph is built correctly"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        assert "step1" in context.dependency_graph
        assert "step2" in context.dependency_graph
        assert "step3" in context.dependency_graph

        assert context.dependency_graph["step1"] == []
        assert context.dependency_graph["step2"] == ["step1"]
        assert context.dependency_graph["step3"] == ["step2"]

    def test_get_ready_steps(self, basic_workflow_config):
        """Test getting ready steps"""
        context = ExecutionContext(workflow_config=basic_workflow_config)

        # Initially, only step1 should be ready (no dependencies)
        ready_steps = context.get_ready_steps()
        assert len(ready_steps) == 1
        assert ready_steps[0] == "step1"

        # After completing step1, step2 should be ready
        context.completed_steps.add("step1")
        context.pending_steps.remove("step1")

        ready_steps = context.get_ready_steps()
        assert len(ready_steps) == 1
        assert ready_steps[0] == "step2"


class TestInputNodeReadyCheck:
    """Tests for input node ready check logic"""

    def test_input_node_ready_with_data(self):
        """Test input node is ready when data is provided"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {
                    "step_id": "input-1",
                    "step_type": "input",
                    "parameters": {"kind": "manual"},
                },
            ],
        }
        context = ExecutionContext(workflow_config=workflow_config)
        context.step_io_data["input-1"] = {"message": "Hello"}

        assert context.can_execute_step("input-1") is True

    def test_input_node_ready_with_trigger_raw(self):
        """Test input node is ready when trigger_raw is provided (backwards compat)"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {
                    "step_id": "input-1",
                    "step_type": "input",
                    "parameters": {"kind": "webhook"},
                },
            ],
        }
        context = ExecutionContext(workflow_config=workflow_config)
        context.step_io_data["trigger_raw"] = {"event": "test"}

        assert context.can_execute_step("input-1") is True

    def test_input_node_not_ready_without_data(self):
        """Test input node is not ready when no data is provided"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {
                    "step_id": "input-1",
                    "step_type": "input",
                    "parameters": {"kind": "manual"},
                },
            ],
        }
        context = ExecutionContext(workflow_config=workflow_config)
        # No data provided

        assert context.can_execute_step("input-1") is False


class TestMergeNodeReadyCheck:
    """Tests for merge node ready check logic"""

    def test_merge_first_available_ready_with_one_dep(self):
        """Test merge node (first_available) is ready when one dependency completes"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {"step_id": "input-1", "step_type": "data_input"},
                {"step_id": "input-2", "step_type": "data_input"},
                {
                    "step_id": "merge-1",
                    "step_type": "merge",
                    "dependencies": ["input-1", "input-2"],
                    "parameters": {"mode": "first_available"},
                },
            ],
        }
        context = ExecutionContext(workflow_config=workflow_config)
        context.completed_steps.add("input-1")  # Only one completed

        assert context.can_execute_step("merge-1") is True

    def test_merge_first_available_not_ready_with_no_deps(self):
        """Test merge node (first_available) is not ready when no dependencies complete"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {"step_id": "input-1", "step_type": "data_input"},
                {"step_id": "input-2", "step_type": "data_input"},
                {
                    "step_id": "merge-1",
                    "step_type": "merge",
                    "dependencies": ["input-1", "input-2"],
                    "parameters": {"mode": "first_available"},
                },
            ],
        }
        context = ExecutionContext(workflow_config=workflow_config)
        # No dependencies completed

        assert context.can_execute_step("merge-1") is False

    def test_merge_wait_all_not_ready_with_one_dep(self):
        """Test merge node (wait_all) is not ready when only one dependency completes"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {"step_id": "input-1", "step_type": "data_input"},
                {"step_id": "input-2", "step_type": "data_input"},
                {
                    "step_id": "merge-1",
                    "step_type": "merge",
                    "dependencies": ["input-1", "input-2"],
                    "parameters": {"mode": "wait_all"},
                },
            ],
        }
        context = ExecutionContext(workflow_config=workflow_config)
        context.completed_steps.add("input-1")  # Only one completed

        assert context.can_execute_step("merge-1") is False

    def test_merge_wait_all_ready_with_all_deps(self):
        """Test merge node (wait_all) is ready when all dependencies complete"""
        workflow_config = {
            "workflow_id": "test",
            "steps": [
                {"step_id": "input-1", "step_type": "data_input"},
                {"step_id": "input-2", "step_type": "data_input"},
                {
                    "step_id": "merge-1",
                    "step_type": "merge",
                    "dependencies": ["input-1", "input-2"],
                    "parameters": {"mode": "wait_all"},
                },
            ],
        }
        context = ExecutionContext(workflow_config=workflow_config)
        context.completed_steps.add("input-1")
        context.completed_steps.add("input-2")

        assert context.can_execute_step("merge-1") is True
