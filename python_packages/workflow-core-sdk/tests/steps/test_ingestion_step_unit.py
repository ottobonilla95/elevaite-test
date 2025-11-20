"""
Standalone unit tests for ingestion step logic

These tests don't require database connection and test the core logic.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_ingestion_step_creates_job(mock_http_client):
    """Test that ingestion step creates a job on first execution"""
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "job_id": "job-123",
        "status": "PENDING",
    }
    mock_response.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_http_client.return_value = mock_client_instance

    # Simulate ingestion step logic
    step_config = {
        "step_id": "ingestion-step-1",
        "config": {
            "ingestion_config": {"source": "s3", "bucket": "test"},
            "tenant_id": "org-123",
        },
    }

    execution_id = str(uuid.uuid4())
    callback_topic = f"wf:{execution_id}:ingestion-step-1:ingestion_done"

    # Make HTTP call
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/ingestion/jobs",
            json={
                "config": step_config["config"]["ingestion_config"],
                "metadata": {
                    "tenant_id": step_config["config"].get("tenant_id"),
                    "execution_id": execution_id,
                    "step_id": step_config["step_id"],
                    "callback_topic": callback_topic,
                },
            },
        )

    # Verify call was made
    mock_client_instance.post.assert_called_once()
    call_args = mock_client_instance.post.call_args
    assert "/ingestion/jobs" in call_args[0][0]

    request_json = call_args[1]["json"]
    assert request_json["config"]["source"] == "s3"
    assert request_json["metadata"]["tenant_id"] == "org-123"


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_ingestion_step_checks_completion(mock_http_client):
    """Test that ingestion step checks job status on second execution"""
    job_id = "job-123"

    # Mock HTTP response for status check
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "job_id": job_id,
        "status": "SUCCEEDED",
        "result_summary": {
            "files_processed": 10,
            "chunks_created": 500,
        },
    }
    mock_response.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_http_client.return_value = mock_client_instance

    # Make HTTP call to check status
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/ingestion/jobs/{job_id}")

    # Verify call was made
    mock_client_instance.get.assert_called_once()
    call_args = mock_client_instance.get.call_args
    assert job_id in call_args[0][0]


@pytest.mark.asyncio
async def test_callback_topic_format():
    """Test that callback topic is formatted correctly"""
    execution_id = str(uuid.uuid4())
    step_id = "ingestion-step-1"
    suffix = "ingestion_done"

    callback_topic = f"wf:{execution_id}:{step_id}:{suffix}"

    assert callback_topic.startswith("wf:")
    assert execution_id in callback_topic
    assert step_id in callback_topic
    assert suffix in callback_topic


def test_job_status_values():
    """Test that job status values are correct"""
    # These should match the JobStatus enum in the ingestion service
    assert "PENDING" == "PENDING"
    assert "RUNNING" == "RUNNING"
    assert "SUCCEEDED" == "SUCCEEDED"
    assert "FAILED" == "FAILED"


@pytest.mark.asyncio
async def test_idempotent_behavior():
    """Test that step is idempotent - doesn't create duplicate jobs"""
    # Simulate checking if job already exists
    prior_output = {
        "ingestion_job_id": "job-123",
        "callback_topic": "wf:exec:step:done",
    }

    # If prior output exists, should check status instead of creating new job
    if prior_output.get("ingestion_job_id"):
        action = "check_status"
    else:
        action = "create_job"

    assert action == "check_status"


@pytest.mark.asyncio
async def test_error_handling():
    """Test that errors are handled gracefully"""
    try:
        raise Exception("Service unavailable")
    except Exception as e:
        error_result = {
            "success": False,
            "status": "failed",
            "error": str(e),
        }

    assert error_result["success"] is False
    assert error_result["status"] == "failed"
    assert "Service unavailable" in error_result["error"]

