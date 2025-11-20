"""
Tests for DBOS ingestion workflows
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from datetime import datetime, timezone

from ingestion_service.workflows import run_ingestion_job, execute_ingestion_pipeline, send_completion_event
from ingestion_service.models import IngestionJob, JobStatus


class TestExecuteIngestionPipeline:
    """Tests for execute_ingestion_pipeline function"""

    @pytest.mark.asyncio
    async def test_execute_pipeline_placeholder(self):
        """Test that pipeline execution placeholder returns expected structure"""
        config = {
            "source": "s3",
            "bucket": "test-bucket",
            "files": ["doc1.pdf", "doc2.pdf"],
        }

        result = await execute_ingestion_pipeline(config)

        assert "files_processed" in result
        assert "chunks_created" in result
        assert "embeddings_generated" in result
        assert result["files_processed"] > 0


class TestSendCompletionEvent:
    """Tests for send_completion_event function"""

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    async def test_send_event_success(self, mock_dbos):
        """Test successful event dispatch"""
        mock_dbos.send_async = AsyncMock()

        callback_topic = "wf:exec-123:step-456:ingestion_done"
        job_id = str(uuid.uuid4())
        status = "SUCCEEDED"
        result_summary = {"files_processed": 10}

        await send_completion_event(callback_topic, job_id, status, result_summary)

        # Verify DBOS.send_async was called
        mock_dbos.send_async.assert_called_once()
        call_args = mock_dbos.send_async.call_args
        assert call_args[1]["topic"] == callback_topic
        
        payload = call_args[1]["message"]
        assert payload["job_id"] == job_id
        assert payload["status"] == status
        assert payload["result_summary"] == result_summary

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    async def test_send_event_no_callback_topic(self, mock_dbos):
        """Test that missing callback_topic is handled gracefully"""
        mock_dbos.send_async = AsyncMock()

        await send_completion_event(None, "job-123", "SUCCEEDED", {})

        # Should not call send_async if no callback_topic
        mock_dbos.send_async.assert_not_called()

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    async def test_send_event_failure_logged(self, mock_dbos):
        """Test that event send failures are logged but don't raise"""
        mock_dbos.send_async = AsyncMock(side_effect=Exception("DBOS error"))

        # Should not raise exception
        await send_completion_event("topic", "job-123", "SUCCEEDED", {})

        mock_dbos.send_async.assert_called_once()


class TestRunIngestionJob:
    """Tests for run_ingestion_job DBOS workflow"""

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    @patch("ingestion_service.workflows.send_completion_event")
    async def test_successful_job_execution(
        self, mock_send_event, mock_execute, mock_get_session, mock_dbos
    ):
        """Test successful job execution flow"""
        # Setup mocks
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Create mock job
        mock_job = IngestionJob(
            id=uuid.UUID(job_id),
            config={"source": "s3", "bucket": "test"},
            status=JobStatus.PENDING,
            callback_topic="wf:exec:step:done",
        )
        mock_session.get.return_value = mock_job
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Mock pipeline execution
        mock_execute.return_value = {
            "files_processed": 10,
            "chunks_created": 500,
            "embeddings_generated": 500,
        }

        mock_send_event.return_value = None

        # Execute workflow
        result = await run_ingestion_job(job_id)

        # Verify result
        assert result["success"] is True
        assert result["job_id"] == job_id
        assert result["status"] == "SUCCEEDED"
        assert result["result_summary"]["files_processed"] == 10

        # Verify job was updated to RUNNING then SUCCEEDED
        assert mock_session.commit.call_count >= 2

        # Verify completion event was sent
        mock_send_event.assert_called_once()

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    async def test_job_not_found(self, mock_get_session, mock_dbos):
        """Test handling of non-existent job"""
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.get.return_value = None

        result = await run_ingestion_job(job_id)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    @patch("ingestion_service.workflows.send_completion_event")
    async def test_pipeline_execution_failure(
        self, mock_send_event, mock_execute, mock_get_session, mock_dbos
    ):
        """Test handling of pipeline execution failure"""
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_job = IngestionJob(
            id=uuid.UUID(job_id),
            config={"source": "s3"},
            status=JobStatus.PENDING,
            callback_topic="wf:exec:step:done",
        )
        mock_session.get.return_value = mock_job
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Mock pipeline failure
        mock_execute.side_effect = Exception("Pipeline error")
        mock_send_event.return_value = None

        result = await run_ingestion_job(job_id)

        # Verify failure result
        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert "Pipeline error" in result["error"]

        # Verify job status was updated to FAILED
        assert mock_job.status == JobStatus.FAILED
        assert "Pipeline error" in mock_job.error_message

        # Verify failure event was sent
        mock_send_event.assert_called_once()
        call_args = mock_send_event.call_args[0]
        assert call_args[2] == "FAILED"  # status argument

