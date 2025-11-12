"""
Unit tests for StepRegistry

Tests step registration, function loading, and execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from workflow_core_sdk.step_registry import StepRegistry, StepExecutionError
from workflow_core_sdk.execution.context_impl import ExecutionContext, StepResult
from workflow_core_sdk.models import StepStatus


@pytest.fixture
def registry():
    """Create a step registry instance"""
    return StepRegistry()


@pytest.fixture
def execution_context():
    """Create a basic execution context"""
    workflow_config = {
        "workflow_id": "test-workflow",
        "name": "Test Workflow",
        "steps": [{"step_id": "step1", "step_type": "test_step"}],
    }
    return ExecutionContext(workflow_config=workflow_config)


class TestStepRegistration:
    """Tests for step registration"""

    @pytest.mark.asyncio
    async def test_register_local_step(self, registry):
        """Test registering a local step"""
        step_config = {
            "step_type": "test_step",
            "name": "Test Step",
            "function_reference": "workflow_core_sdk.steps.data_steps.data_input_step",
            "execution_type": "local",
            "description": "A test step",
        }

        step_id = await registry.register_step(step_config)

        assert step_id is not None
        assert "test_step" in registry.registered_steps
        assert registry.registered_steps["test_step"]["step_type"] == "test_step"
        assert registry.registered_steps["test_step"]["execution_type"] == "local"
        assert "test_step" in registry.step_functions

    @pytest.mark.asyncio
    async def test_register_rpc_step(self, registry):
        """Test registering an RPC step"""
        step_config = {
            "step_type": "rpc_step",
            "name": "RPC Step",
            "function_reference": "http://example.com/step",
            "execution_type": "rpc",
            "endpoint_config": {"url": "http://example.com/step", "timeout": 30},
        }

        step_id = await registry.register_step(step_config)

        assert step_id is not None
        assert "rpc_step" in registry.registered_steps
        assert registry.registered_steps["rpc_step"]["execution_type"] == "rpc"
        # RPC steps don't load functions locally
        assert "rpc_step" not in registry.step_functions

    @pytest.mark.asyncio
    async def test_register_step_missing_required_field(self, registry):
        """Test registering a step with missing required field"""
        step_config = {
            "step_type": "incomplete_step",
            "name": "Incomplete Step",
            # Missing function_reference and execution_type
        }

        with pytest.raises(ValueError, match="Missing required field"):
            await registry.register_step(step_config)

    @pytest.mark.asyncio
    async def test_register_step_invalid_function_reference(self, registry):
        """Test registering a step with invalid function reference"""
        step_config = {
            "step_type": "invalid_step",
            "name": "Invalid Step",
            "function_reference": "invalid_module.invalid_function",
            "execution_type": "local",
        }

        with pytest.raises(StepExecutionError, match="Failed to load function"):
            await registry.register_step(step_config)


class TestStepExecution:
    """Tests for step execution"""

    @pytest.mark.asyncio
    async def test_execute_local_step_success(self, registry, execution_context):
        """Test executing a local step successfully"""

        # Create a mock step function
        async def mock_step(step_config, input_data, execution_context):
            return {"result": "success", "data": input_data.get("value", 0) * 2}

        # Register the step manually
        registry.registered_steps["test_step"] = {
            "step_id": "test-step-id",
            "step_type": "test_step",
            "name": "Test Step",
            "execution_type": "local",
            "function_reference": "mock.function",
            "parameters_schema": {},
            "output_schema": {},
            "endpoint_config": {},
            "tags": [],
            "registered_at": "2024-01-01T00:00:00",
        }
        registry.step_functions["test_step"] = mock_step

        # Execute the step
        step_config = {"step_id": "step1", "step_type": "test_step"}
        input_data = {"value": 21}

        result = await registry.execute_step("test_step", step_config, input_data, execution_context)

        assert isinstance(result, StepResult)
        assert result.status == StepStatus.COMPLETED
        assert result.output_data["result"] == "success"
        assert result.output_data["data"] == 42
        assert result.execution_time_ms is not None

    @pytest.mark.asyncio
    async def test_execute_local_step_returns_step_result(self, registry, execution_context):
        """Test executing a local step that returns StepResult"""

        # Create a mock step function that returns StepResult
        async def mock_step(step_config, input_data, execution_context):
            return StepResult(
                step_id=step_config["step_id"],
                status=StepStatus.WAITING,
                output_data={"status": "waiting", "message": "Waiting for approval"},
            )

        # Register the step
        registry.registered_steps["waiting_step"] = {
            "step_id": "waiting-step-id",
            "step_type": "waiting_step",
            "name": "Waiting Step",
            "execution_type": "local",
            "function_reference": "mock.function",
            "parameters_schema": {},
            "output_schema": {},
            "endpoint_config": {},
            "tags": [],
            "registered_at": "2024-01-01T00:00:00",
        }
        registry.step_functions["waiting_step"] = mock_step

        # Execute the step
        step_config = {"step_id": "step1", "step_type": "waiting_step"}
        input_data = {}

        result = await registry.execute_step("waiting_step", step_config, input_data, execution_context)

        assert isinstance(result, StepResult)
        assert result.status == StepStatus.WAITING
        assert result.output_data["message"] == "Waiting for approval"

    @pytest.mark.asyncio
    async def test_execute_local_step_failure(self, registry, execution_context):
        """Test executing a local step that fails"""

        # Create a mock step function that raises an exception
        async def mock_step(step_config, input_data, execution_context):
            raise ValueError("Step execution failed")

        # Register the step
        registry.registered_steps["failing_step"] = {
            "step_id": "failing-step-id",
            "step_type": "failing_step",
            "name": "Failing Step",
            "execution_type": "local",
            "function_reference": "mock.function",
            "parameters_schema": {},
            "output_schema": {},
            "endpoint_config": {},
            "tags": [],
            "registered_at": "2024-01-01T00:00:00",
        }
        registry.step_functions["failing_step"] = mock_step

        # Execute the step
        step_config = {"step_id": "step1", "step_type": "failing_step"}
        input_data = {}

        result = await registry.execute_step("failing_step", step_config, input_data, execution_context)

        assert isinstance(result, StepResult)
        assert result.status == StepStatus.FAILED
        assert "Step execution failed" in result.error_message
        assert result.execution_time_ms is not None

    @pytest.mark.asyncio
    async def test_execute_unknown_step_type(self, registry, execution_context):
        """Test executing an unknown step type"""
        step_config = {"step_id": "step1", "step_type": "unknown_step"}
        input_data = {}

        with pytest.raises(StepExecutionError, match="Unknown step type"):
            await registry.execute_step("unknown_step", step_config, input_data, execution_context)

    @pytest.mark.asyncio
    async def test_execute_sync_function(self, registry, execution_context):
        """Test executing a synchronous step function"""

        # Create a synchronous mock step function
        def sync_mock_step(step_config, input_data, execution_context):
            return {"result": "sync success"}

        # Register the step
        registry.registered_steps["sync_step"] = {
            "step_id": "sync-step-id",
            "step_type": "sync_step",
            "name": "Sync Step",
            "execution_type": "local",
            "function_reference": "mock.function",
            "parameters_schema": {},
            "output_schema": {},
            "endpoint_config": {},
            "tags": [],
            "registered_at": "2024-01-01T00:00:00",
        }
        registry.step_functions["sync_step"] = sync_mock_step

        # Execute the step
        step_config = {"step_id": "step1", "step_type": "sync_step"}
        input_data = {}

        result = await registry.execute_step("sync_step", step_config, input_data, execution_context)

        assert isinstance(result, StepResult)
        assert result.status == StepStatus.COMPLETED
        assert result.output_data["result"] == "sync success"


class TestStepListing:
    """Tests for step listing and querying"""

    @pytest.mark.asyncio
    async def test_list_registered_steps(self, registry):
        """Test listing all registered steps"""
        # Register multiple steps
        step_configs = [
            {
                "step_type": "step1",
                "name": "Step 1",
                "function_reference": "workflow_core_sdk.steps.data_steps.data_input_step",
                "execution_type": "local",
            },
            {
                "step_type": "step2",
                "name": "Step 2",
                "function_reference": "http://example.com/step2",
                "execution_type": "rpc",
                "endpoint_config": {"url": "http://example.com/step2"},
            },
        ]

        for config in step_configs:
            await registry.register_step(config)

        # List all steps
        steps = await registry.get_registered_steps()

        assert len(steps) == 2
        assert any(s["step_type"] == "step1" for s in steps)
        assert any(s["step_type"] == "step2" for s in steps)

    @pytest.mark.asyncio
    async def test_get_step_info(self, registry):
        """Test getting info for a specific step"""
        step_config = {
            "step_type": "test_step",
            "name": "Test Step",
            "function_reference": "workflow_core_sdk.steps.data_steps.data_input_step",
            "execution_type": "local",
            "description": "A test step",
        }

        await registry.register_step(step_config)

        # Get step info
        info = await registry.get_step_info("test_step")

        assert info is not None
        assert info["step_type"] == "test_step"
        assert info["name"] == "Test Step"
        assert info["description"] == "A test step"

    @pytest.mark.asyncio
    async def test_get_step_info_not_found(self, registry):
        """Test getting info for non-existent step"""
        info = await registry.get_step_info("nonexistent_step")
        assert info is None
