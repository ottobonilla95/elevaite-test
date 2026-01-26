"""
Tests for ExecutionService

This module tests the ExecutionService which provides programmatic workflow execution
without HTTP request handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from sqlmodel import Session

from workflow_core_sdk.services.execution_service import ExecutionService


@pytest.mark.asyncio
async def test_execute_workflow_not_found():
    """Test that execute_workflow raises ValueError when workflow not found"""
    from unittest.mock import patch

    # Mock session and workflow engine
    mock_session = Mock(spec=Session)
    mock_engine = Mock()

    with patch("workflow_core_sdk.services.execution_service.DatabaseService") as MockDB:
        mock_db = MockDB.return_value
        mock_db.get_workflow.return_value = None  # Workflow not found

        # Test with non-existent workflow (use valid UUID format)
        with pytest.raises(ValueError, match="Workflow not found"):
            await ExecutionService.execute_workflow(
                workflow_id="00000000-0000-0000-0000-000000000000",
                session=mock_session,
                workflow_engine=mock_engine,
                backend="local",
            )


@pytest.mark.asyncio
async def test_execute_workflow_invalid_backend():
    """Test that execute_workflow raises ValueError for invalid backend"""
    # Mock session and workflow engine
    mock_session = Mock(spec=Session)
    mock_engine = Mock()

    # Mock DatabaseService to return a workflow
    from unittest.mock import patch

    with patch("workflow_core_sdk.services.execution_service.DatabaseService") as MockDB:
        mock_db = MockDB.return_value
        mock_db.get_workflow.return_value = {
            "id": "test-workflow-id",
            "name": "Test Workflow",
            "steps": [],
        }

        # Test with invalid backend
        with pytest.raises(ValueError, match="Invalid execution backend"):
            await ExecutionService.execute_workflow(
                workflow_id="test-workflow-id",
                session=mock_session,
                workflow_engine=mock_engine,
                backend="invalid-backend",
            )


@pytest.mark.asyncio
async def test_execute_workflow_local_backend():
    """Test workflow execution with local backend"""
    from unittest.mock import patch

    # Mock session and workflow engine
    mock_session = Mock(spec=Session)
    mock_engine = Mock()
    mock_engine.execute_workflow = AsyncMock()

    with patch("workflow_core_sdk.services.execution_service.DatabaseService") as MockDB:
        mock_db = MockDB.return_value
        mock_db.get_workflow.return_value = {
            "id": "test-workflow-id",
            "name": "Test Workflow",
            "steps": [
                {
                    "step_id": "step-1",
                    "step_type": "tool",
                    "parameters": {},
                }
            ],
        }
        mock_db.create_execution.return_value = "execution-123"

        # Execute workflow
        execution_id = await ExecutionService.execute_workflow(
            workflow_id="test-workflow-id",
            session=mock_session,
            workflow_engine=mock_engine,
            backend="local",
            wait=True,
            metadata={"source": "test"},
        )

        # Verify execution was created
        assert execution_id == "execution-123"
        mock_db.create_execution.assert_called_once()

        # Verify workflow engine was called
        mock_engine.execute_workflow.assert_called_once()


@pytest.mark.asyncio
async def test_execute_workflow_with_trigger_payload():
    """Test workflow execution with custom trigger payload"""
    from unittest.mock import patch

    # Mock session and workflow engine
    mock_session = Mock(spec=Session)
    mock_engine = Mock()
    mock_engine.execute_workflow = AsyncMock()

    with patch("workflow_core_sdk.services.execution_service.DatabaseService") as MockDB:
        mock_db = MockDB.return_value
        mock_db.get_workflow.return_value = {
            "id": "test-workflow-id",
            "name": "Test Workflow",
            "steps": [],
        }
        mock_db.create_execution.return_value = "execution-456"

        # Custom trigger payload
        trigger_payload = {
            "kind": "chat",
            "current_message": "Hello, world!",
            "history": [],
        }

        # Execute workflow
        execution_id = await ExecutionService.execute_workflow(
            workflow_id="test-workflow-id",
            session=mock_session,
            workflow_engine=mock_engine,
            backend="local",
            trigger_payload=trigger_payload,
            wait=True,
        )

        # Verify execution was created
        assert execution_id == "execution-456"

        # Verify workflow engine was called with correct context
        mock_engine.execute_workflow.assert_called_once()
        call_args = mock_engine.execute_workflow.call_args
        execution_context = call_args[0][0]

        # Verify trigger payload was set
        assert execution_context.step_io_data["trigger_raw"] == trigger_payload


@pytest.mark.asyncio
async def test_execute_workflow_default_trigger():
    """Test that default webhook trigger is used when no trigger_payload provided"""
    from unittest.mock import patch

    # Mock session and workflow engine
    mock_session = Mock(spec=Session)
    mock_engine = Mock()
    mock_engine.execute_workflow = AsyncMock()

    with patch("workflow_core_sdk.services.execution_service.DatabaseService") as MockDB:
        mock_db = MockDB.return_value
        mock_db.get_workflow.return_value = {
            "id": "test-workflow-id",
            "name": "Test Workflow",
            "steps": [],
        }
        mock_db.create_execution.return_value = "execution-789"

        # Execute workflow without trigger payload
        execution_id = await ExecutionService.execute_workflow(
            workflow_id="test-workflow-id",
            session=mock_session,
            workflow_engine=mock_engine,
            backend="local",
            wait=True,
            metadata={"source": "scheduler"},
        )

        # Verify execution was created
        assert execution_id == "execution-789"

        # Verify workflow engine was called
        mock_engine.execute_workflow.assert_called_once()
        call_args = mock_engine.execute_workflow.call_args
        execution_context = call_args[0][0]

        # Verify default webhook trigger was set
        trigger = execution_context.step_io_data["trigger_raw"]
        assert trigger["kind"] == "webhook"
        assert trigger["data"]["source"] == "scheduler"
