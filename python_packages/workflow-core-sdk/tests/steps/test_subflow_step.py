"""
Unit tests for subflow_step

Tests subflow execution with input/output mapping and context inheritance.
"""

import pytest
from unittest.mock import MagicMock

from workflow_core_sdk.steps.flow_steps import subflow_step
from workflow_core_sdk.execution_context import (
    ExecutionContext,
    ExecutionStatus,
    UserContext,
)


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

    @pytest.mark.asyncio
    async def test_missing_workflow_engine(self, execution_context):
        """Test error when workflow engine is not available"""
        execution_context.workflow_engine = None
        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {"workflow_id": "test-subflow"},
        }

        # Mock the database service to return a workflow
        from unittest.mock import patch, MagicMock

        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [],
        }

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, {}, execution_context)

        assert result["success"] is False
        assert "Workflow engine not available" in result["error"]


class TestSubflowExecution:
    """Tests for subflow execution"""

    @pytest.mark.asyncio
    async def test_successful_subflow_execution(self, execution_context):
        """Test successful subflow execution"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {"workflow_id": "test-subflow"},
        }
        input_data = {"message": "Hello"}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [{"step_id": "step1", "step_type": "data_input"}],
        }

        # Mock the workflow engine execution
        mock_completed_context = MagicMock()
        mock_completed_context.execution_id = "subflow-execution-id"
        mock_completed_context.status = ExecutionStatus.COMPLETED
        mock_completed_context.step_io_data = {"result": "success"}

        execution_context.workflow_engine.execute_workflow = AsyncMock(
            return_value=mock_completed_context
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is True
        assert result["subflow_id"] == "test-subflow"
        assert result["subflow_execution_id"] == "subflow-execution-id"
        assert result["subflow_status"] == "completed"
        assert result["subflow_output"] == {"result": "success"}
        assert "execution_time_seconds" in result
        assert "started_at" in result
        assert "completed_at" in result

    @pytest.mark.asyncio
    async def test_subflow_execution_failure(self, execution_context):
        """Test subflow execution failure"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {"workflow_id": "test-subflow"},
        }
        input_data = {"message": "Hello"}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [{"step_id": "step1", "step_type": "data_input"}],
        }

        # Mock the workflow engine to raise an exception
        execution_context.workflow_engine.execute_workflow = AsyncMock(
            side_effect=Exception("Subflow execution failed")
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is False
        assert result["subflow_id"] == "test-subflow"
        assert result["subflow_status"] == "failed"
        assert "Subflow execution failed" in result["error"]
        assert "execution_time_seconds" in result
        assert "started_at" in result
        assert "failed_at" in result


class TestSubflowInputMapping:
    """Tests for subflow input mapping"""

    @pytest.mark.asyncio
    async def test_input_mapping_simple(self, execution_context):
        """Test simple input mapping"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {
                "workflow_id": "test-subflow",
                "input_mapping": {"user_name": "user.name", "user_age": "user.age"},
            },
        }
        input_data = {"user": {"name": "John", "age": 30}, "extra": "data"}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [],
        }

        # Mock the workflow engine
        mock_completed_context = MagicMock()
        mock_completed_context.execution_id = "subflow-execution-id"
        mock_completed_context.status = ExecutionStatus.COMPLETED
        mock_completed_context.step_io_data = {}

        execution_context.workflow_engine.execute_workflow = AsyncMock(
            return_value=mock_completed_context
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is True
        # Verify the subflow was called with mapped input
        call_args = execution_context.workflow_engine.execute_workflow.call_args
        subflow_context = call_args[0][0]
        assert subflow_context.step_io_data["subflow_input"] == {
            "user_name": "John",
            "user_age": 30,
        }

    @pytest.mark.asyncio
    async def test_input_mapping_missing_field(self, execution_context):
        """Test input mapping with missing field"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {
                "workflow_id": "test-subflow",
                "input_mapping": {"user_email": "user.email"},
            },
        }
        input_data = {"user": {"name": "John"}}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [],
        }

        # Mock the workflow engine
        mock_completed_context = MagicMock()
        mock_completed_context.execution_id = "subflow-execution-id"
        mock_completed_context.status = ExecutionStatus.COMPLETED
        mock_completed_context.step_io_data = {}

        execution_context.workflow_engine.execute_workflow = AsyncMock(
            return_value=mock_completed_context
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is True
        # Verify the subflow was called with empty input (missing field not mapped)
        call_args = execution_context.workflow_engine.execute_workflow.call_args
        subflow_context = call_args[0][0]
        assert subflow_context.step_io_data["subflow_input"] == {}


class TestSubflowOutputMapping:
    """Tests for subflow output mapping"""

    @pytest.mark.asyncio
    async def test_output_mapping_simple(self, execution_context):
        """Test simple output mapping"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {
                "workflow_id": "test-subflow",
                "output_mapping": {
                    "final_result": "step1.result",
                    "status": "step1.status",
                },
            },
        }
        input_data = {"message": "Hello"}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [],
        }

        # Mock the workflow engine
        mock_completed_context = MagicMock()
        mock_completed_context.execution_id = "subflow-execution-id"
        mock_completed_context.status = ExecutionStatus.COMPLETED
        mock_completed_context.step_io_data = {
            "step1": {"result": "success", "status": "completed"},
            "step2": {"data": "extra"},
        }

        execution_context.workflow_engine.execute_workflow = AsyncMock(
            return_value=mock_completed_context
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is True
        assert result["subflow_output"] == {
            "final_result": "success",
            "status": "completed",
        }

    @pytest.mark.asyncio
    async def test_output_mapping_no_mapping(self, execution_context):
        """Test output with no mapping returns all data"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {"workflow_id": "test-subflow"},
        }
        input_data = {"message": "Hello"}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [],
        }

        # Mock the workflow engine
        mock_completed_context = MagicMock()
        mock_completed_context.execution_id = "subflow-execution-id"
        mock_completed_context.status = ExecutionStatus.COMPLETED
        mock_completed_context.step_io_data = {
            "step1": {"result": "success"},
            "step2": {"data": "extra"},
        }

        execution_context.workflow_engine.execute_workflow = AsyncMock(
            return_value=mock_completed_context
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is True
        # Without mapping, all step_io_data should be returned
        assert result["subflow_output"] == {
            "step1": {"result": "success"},
            "step2": {"data": "extra"},
        }


class TestSubflowContextInheritance:
    """Tests for subflow context inheritance"""

    @pytest.mark.asyncio
    async def test_context_inheritance_enabled(self, execution_context, user_context):
        """Test subflow inherits user context when enabled"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {"workflow_id": "test-subflow", "inherit_context": True},
        }
        input_data = {"message": "Hello"}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [],
        }

        # Mock the workflow engine
        mock_completed_context = MagicMock()
        mock_completed_context.execution_id = "subflow-execution-id"
        mock_completed_context.status = ExecutionStatus.COMPLETED
        mock_completed_context.step_io_data = {}

        execution_context.workflow_engine.execute_workflow = AsyncMock(
            return_value=mock_completed_context
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is True
        # Verify the subflow context inherited the user context
        call_args = execution_context.workflow_engine.execute_workflow.call_args
        subflow_context = call_args[0][0]
        assert subflow_context.user_context == user_context

    @pytest.mark.asyncio
    async def test_context_inheritance_disabled(self, execution_context, user_context):
        """Test subflow creates isolated context when inheritance disabled"""
        from unittest.mock import patch, MagicMock, AsyncMock

        config = {
            "step_id": "subflow-step-1",
            "step_type": "subflow",
            "config": {"workflow_id": "test-subflow", "inherit_context": False},
        }
        input_data = {"message": "Hello"}

        # Mock the database service
        mock_workflow = {
            "workflow_id": "test-subflow",
            "name": "Test Subflow",
            "steps": [],
        }

        # Mock the workflow engine
        mock_completed_context = MagicMock()
        mock_completed_context.execution_id = "subflow-execution-id"
        mock_completed_context.status = ExecutionStatus.COMPLETED
        mock_completed_context.step_io_data = {}

        execution_context.workflow_engine.execute_workflow = AsyncMock(
            return_value=mock_completed_context
        )

        with patch("workflow_core_sdk.db.service.DatabaseService") as mock_db_service:
            mock_db_instance = MagicMock()
            mock_db_instance.get_workflow.return_value = mock_workflow
            mock_db_service.return_value = mock_db_instance

            result = await subflow_step(config, input_data, execution_context)

        assert result["success"] is True
        # Verify the subflow context has isolated user context
        call_args = execution_context.workflow_engine.execute_workflow.call_args
        subflow_context = call_args[0][0]
        assert subflow_context.user_context != user_context
        assert subflow_context.user_context.user_id.startswith("subflow-")
        assert (
            subflow_context.user_context.organization_id == user_context.organization_id
        )
