"""
Integration tests for ingestion workflow

Tests the end-to-end flow of an ingestion step in a workflow.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
import asyncio

from workflow_core_sdk.dbos_impl.workflows import dbos_execute_workflow_durable
from workflow_core_sdk.execution_context import ExecutionContext


@pytest.mark.asyncio
@patch("workflow_core_sdk.dbos_impl.workflows.get_dbos_adapter")
@patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
@patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
@patch("workflow_core_sdk.dbos_impl.workflows.stream_manager")
async def test_ingestion_workflow_integration(
    mock_wf_stream, mock_step_stream, mock_http_client, mock_get_adapter
):
    """
    Test that a workflow with an ingestion step:
    1. Creates an ingestion job
    2. Returns status="ingesting" (not WAITING)
    3. Blocks on callback topic
    4. Receives completion event
    5. Completes successfully
    """
    # Mock DBOS adapter
    mock_adapter = MagicMock()
    mock_adapter.logger = MagicMock()
    mock_get_adapter.return_value = mock_adapter

    # Mock stream managers
    mock_step_stream.emit_execution_event = AsyncMock()
    mock_step_stream.emit_workflow_event = AsyncMock()
    mock_wf_stream.emit_execution_event = AsyncMock()
    mock_wf_stream.emit_workflow_event = AsyncMock()

    # Mock HTTP client for job creation
    job_id = str(uuid.uuid4())
    mock_create_response = MagicMock()
    mock_create_response.json.return_value = {
        "job_id": job_id,
        "status": "PENDING",
    }
    mock_create_response.raise_for_status = MagicMock()

    # Mock HTTP client for job status check
    mock_status_response = MagicMock()
    mock_status_response.json.return_value = {
        "job_id": job_id,
        "status": "SUCCEEDED",
        "result_summary": {
            "files_processed": 10,
            "chunks_created": 500,
        },
    }
    mock_status_response.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_create_response)
    mock_client_instance.get = AsyncMock(return_value=mock_status_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_http_client.return_value = mock_client_instance

    # Mock DBOS recv_async to simulate event arrival
    event_received = False

    async def mock_recv_async(topic, timeout_seconds):
        nonlocal event_received
        if not event_received:
            event_received = True
            # Simulate event arrival after short delay
            await asyncio.sleep(0.1)
            return {"job_id": job_id, "status": "SUCCEEDED"}
        return None

    # Define workflow with ingestion step
    workflow_config = {
        "workflow_id": str(uuid.uuid4()),
        "steps": [
            {
                "step_id": "ingestion-step",
                "step_type": "ingestion",
                "config": {
                    "ingestion_config": {
                        "source": "s3",
                        "bucket": "test-bucket",
                    },
                    "tenant_id": "org-123",
                },
            }
        ],
    }

    trigger_data = {"message": "Start ingestion"}
    user_context = {"user_id": "test-user"}

    # Note: This is a simplified test that mocks the DBOS workflow execution
    # A full integration test would require a running DBOS instance

    # For now, we verify that the ingestion step can be executed
    # and returns the expected status="ingesting" on first call

    from workflow_core_sdk.steps.ingestion_steps import ingestion_step

    step_config = workflow_config["steps"][0]
    execution_context = ExecutionContext(
        workflow_config=workflow_config,
        user_context=user_context,
        execution_id=str(uuid.uuid4()),
    )
    execution_context.workflow_id = workflow_config["workflow_id"]
    execution_context.step_io_data = {}

    # First execution - should create job and return ingesting
    result1 = await ingestion_step(step_config, trigger_data, execution_context)

    assert result1["success"] is False
    assert result1["status"] == "ingesting"
    assert "ingestion_job_id" in result1["output_data"]
    assert "callback_topic" in result1["output_data"]

    # Simulate storing output_data
    execution_context.step_io_data["ingestion-step"] = result1["output_data"]

    # Second execution - should check status and return success
    result2 = await ingestion_step(step_config, trigger_data, execution_context)

    assert result2["success"] is True
    assert result2["status"] == "completed"
    assert result2["output_data"]["ingestion_job_id"] == job_id
    assert "result_summary" in result2["output_data"]


@pytest.mark.asyncio
@patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
@patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
async def test_ingestion_step_idempotency(mock_stream, mock_http_client):
    """Test that ingestion step is idempotent"""
    mock_stream.emit_execution_event = AsyncMock()
    mock_stream.emit_workflow_event = AsyncMock()

    job_id = str(uuid.uuid4())

    # Mock HTTP responses
    mock_create_response = MagicMock()
    mock_create_response.json.return_value = {"job_id": job_id, "status": "PENDING"}
    mock_create_response.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_create_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_http_client.return_value = mock_client_instance

    from workflow_core_sdk.steps.ingestion_steps import ingestion_step

    step_config = {
        "step_id": "ingestion-step",
        "step_type": "ingestion",
        "config": {"ingestion_config": {"source": "s3"}},
    }

    execution_context = ExecutionContext(
        workflow_config={"workflow_id": str(uuid.uuid4())},
        user_context={"user_id": "test-user"},
        execution_id=str(uuid.uuid4()),
    )
    execution_context.workflow_id = str(uuid.uuid4())
    execution_context.step_io_data = {}

    # First call - creates job
    result1 = await ingestion_step(step_config, {}, execution_context)
    assert result1["status"] == "ingesting"
    assert mock_client_instance.post.call_count == 1

    # Store output
    execution_context.step_io_data["ingestion-step"] = result1["output_data"]

    # Second call with same context - should NOT create another job
    # (This would happen after DBOS event is received)
    result2 = await ingestion_step(step_config, {}, execution_context)

    # Should still only have 1 POST call (job creation)
    assert mock_client_instance.post.call_count == 1

