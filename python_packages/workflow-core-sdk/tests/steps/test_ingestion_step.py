"""
Unit tests for ingestion_step

Tests the two-phase execution behavior of the ingestion step.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid

from workflow_core_sdk.steps.ingestion_steps import ingestion_step
from workflow_core_sdk.execution_context import ExecutionContext


@pytest.fixture
def execution_context():
    """Create a mock execution context"""
    context = ExecutionContext(
        workflow_config={"workflow_id": str(uuid.uuid4())},
        user_context={"user_id": "test-user"},
        execution_id=str(uuid.uuid4()),
    )
    context.workflow_id = str(uuid.uuid4())
    context.step_io_data = {}
    return context


@pytest.fixture
def step_config():
    """Basic step configuration"""
    return {
        "step_id": "ingestion-step-1",
        "step_type": "ingestion",
        "config": {
            "ingestion_config": {
                "source": "s3",
                "bucket": "test-bucket",
            },
            "tenant_id": "org-123",
        },
    }


class TestIngestionStepFirstExecution:
    """Tests for first execution (job creation)"""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    @patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
    async def test_creates_job_successfully(
        self, mock_stream, mock_http_client, step_config, execution_context
    ):
        """Test that first execution creates an ingestion job"""
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

        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Execute step
        result = await ingestion_step(step_config, {}, execution_context)

        # Verify result
        assert result["success"] is False
        assert result["status"] == "ingesting"
        assert "ingestion_job_id" in result["output_data"]
        assert result["output_data"]["ingestion_job_id"] == "job-123"
        assert "callback_topic" in result["output_data"]

        # Verify HTTP call
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert "/ingestion/jobs" in call_args[0][0]

        # Verify request payload
        request_json = call_args[1]["json"]
        assert "config" in request_json
        assert request_json["config"] == step_config["config"]["ingestion_config"]
        assert request_json["metadata"]["tenant_id"] == "org-123"
        assert (
            request_json["metadata"]["execution_id"] == execution_context.execution_id
        )
        assert request_json["metadata"]["step_id"] == "ingestion-step-1"
        assert "callback_topic" in request_json["metadata"]

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    @patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
    async def test_handles_job_creation_failure(
        self, mock_stream, mock_http_client, step_config, execution_context
    ):
        """Test error handling when job creation fails"""
        # Mock HTTP error
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=Exception("Service unavailable")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Execute step
        result = await ingestion_step(step_config, {}, execution_context)

        # Verify error result
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "error" in result
        assert "Service unavailable" in result["error"]


class TestIngestionStepSecondExecution:
    """Tests for second execution (completion check)"""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    async def test_checks_job_completion_success(
        self, mock_http_client, step_config, execution_context
    ):
        """Test that second execution checks job status and returns success"""
        # Set up prior output (job already created)
        execution_context.step_io_data["ingestion-step-1"] = {
            "ingestion_job_id": "job-123",
            "callback_topic": "wf:exec:step:ingestion_done",
        }

        # Mock HTTP response for job status
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "job_id": "job-123",
            "status": "SUCCEEDED",
            "result_summary": {
                "files_processed": 10,
                "chunks_created": 500,
            },
            "completed_at": "2024-01-01T00:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        # Execute step (second time)
        result = await ingestion_step(step_config, {}, execution_context)

        # Verify success result
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["output_data"]["ingestion_job_id"] == "job-123"
        assert "result_summary" in result["output_data"]
        assert result["output_data"]["result_summary"]["files_processed"] == 10

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    async def test_checks_job_completion_failure(
        self, mock_http_client, step_config, execution_context
    ):
        """Test that second execution handles job failure"""
        # Set up prior output
        execution_context.step_io_data["ingestion-step-1"] = {
            "ingestion_job_id": "job-123",
            "callback_topic": "wf:exec:step:ingestion_done",
        }

        # Mock HTTP response for failed job
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "job_id": "job-123",
            "status": "FAILED",
            "error_message": "Ingestion pipeline error",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        # Execute step
        result = await ingestion_step(step_config, {}, execution_context)

        # Verify failure result
        assert result["success"] is False
        assert result["status"] == "failed"
        assert "error" in result
        assert "Ingestion pipeline error" in result["error"]


class TestIngestionStepEdgeCases:
    """Tests for edge cases in ingestion step"""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    @patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
    async def test_missing_ingestion_service_url(
        self, mock_stream, mock_http_client, step_config, execution_context
    ):
        """Test handling when INGESTION_SERVICE_URL is not configured"""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        with patch.dict("os.environ", {}, clear=True):
            # Should use default localhost URL
            mock_response = MagicMock()
            mock_response.json.return_value = {"job_id": "job-123", "status": "PENDING"}
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_http_client.return_value = mock_client_instance

            result = await ingestion_step(step_config, {}, execution_context)

            assert result["status"] == "ingesting"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    @patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
    async def test_job_status_still_running(
        self, mock_stream, mock_http_client, step_config, execution_context
    ):
        """Test checking job status when job is still running"""
        execution_context.step_io_data["ingestion-step-1"] = {
            "ingestion_job_id": "job-123",
            "callback_topic": "wf:exec:step:ingestion_done",
        }

        # Mock HTTP response for job still running
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "job_id": "job-123",
            "status": "RUNNING",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        result = await ingestion_step(step_config, {}, execution_context)

        # Should return ingesting status (not success)
        assert result["success"] is False
        assert result["status"] == "ingesting"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    @patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
    async def test_http_timeout(
        self, mock_stream, mock_http_client, step_config, execution_context
    ):
        """Test handling of HTTP timeout"""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        import httpx

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        result = await ingestion_step(step_config, {}, execution_context)

        assert result["success"] is False
        assert result["status"] == "failed"
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    @patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
    async def test_http_404_error(
        self, mock_stream, mock_http_client, step_config, execution_context
    ):
        """Test handling of 404 error from ingestion service"""
        execution_context.step_io_data["ingestion-step-1"] = {
            "ingestion_job_id": "job-nonexistent",
            "callback_topic": "wf:exec:step:ingestion_done",
        }

        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )
        )

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        result = await ingestion_step(step_config, {}, execution_context)

        assert result["success"] is False
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.ingestion_steps.httpx.AsyncClient")
    @patch("workflow_core_sdk.steps.ingestion_steps.stream_manager")
    async def test_missing_tenant_id(
        self, mock_stream, mock_http_client, execution_context
    ):
        """Test that tenant_id is optional"""
        step_config = {
            "step_id": "ingestion-step-1",
            "step_type": "ingestion",
            "config": {
                "ingestion_config": {"source": "s3"},
                # No tenant_id
            },
        }

        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {"job_id": "job-123", "status": "PENDING"}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        result = await ingestion_step(step_config, {}, execution_context)

        assert result["status"] == "ingesting"

        # Verify request was made without tenant_id
        call_args = mock_client_instance.post.call_args
        request_json = call_args[1]["json"]
        assert request_json["metadata"].get("tenant_id") is None
