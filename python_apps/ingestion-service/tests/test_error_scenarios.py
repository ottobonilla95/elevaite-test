"""
Tests for error scenarios and edge cases
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid

from ingestion_service.workflows import run_ingestion_job, send_completion_event
from ingestion_service.models import IngestionJob, JobStatus


class TestWorkflowErrorHandling:
    """Tests for error handling in DBOS workflows"""

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    async def test_database_session_failure(self, mock_get_session, mock_dbos):
        """Test handling of database session failure"""
        mock_get_session.side_effect = Exception("Database connection lost")

        job_id = str(uuid.uuid4())
        result = await run_ingestion_job(job_id)

        assert result["success"] is False
        assert "error" in result
        assert "Database connection lost" in result["error"]

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    async def test_pipeline_timeout(self, mock_execute, mock_get_session, mock_dbos):
        """Test handling of pipeline execution timeout"""
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

        # Simulate timeout
        import asyncio

        mock_execute.side_effect = asyncio.TimeoutError("Pipeline execution timed out")

        result = await run_ingestion_job(job_id)

        assert result["success"] is False
        assert result["status"] == "FAILED"
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    async def test_partial_pipeline_failure(self, mock_execute, mock_get_session, mock_dbos):
        """Test handling of partial pipeline failure (some files processed, then error)"""
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_job = IngestionJob(
            id=uuid.UUID(job_id),
            config={"source": "s3", "files": ["doc1.pdf", "doc2.pdf", "doc3.pdf"]},
            status=JobStatus.PENDING,
            callback_topic="wf:exec:step:done",
        )
        mock_session.get.return_value = mock_job
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Simulate partial success
        mock_execute.side_effect = Exception("Failed on file 3 of 3")

        result = await run_ingestion_job(job_id)

        assert result["success"] is False
        assert "Failed on file 3" in result["error"]

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    @patch("ingestion_service.workflows.send_completion_event")
    async def test_event_send_failure_does_not_fail_job(
        self, mock_send_event, mock_execute, mock_get_session, mock_dbos
    ):
        """Test that event send failure doesn't fail the job itself"""
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

        mock_execute.return_value = {"files_processed": 10}

        # Event send fails
        mock_send_event.side_effect = Exception("DBOS event system down")

        result = await run_ingestion_job(job_id)

        # Job should still succeed
        assert result["success"] is True
        assert result["status"] == "SUCCEEDED"


class TestEdgeCases:
    """Tests for edge cases"""

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    async def test_empty_config(self, mock_execute, mock_get_session, mock_dbos):
        """Test handling of empty configuration"""
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_job = IngestionJob(
            id=uuid.UUID(job_id),
            config={},  # Empty config
            status=JobStatus.PENDING,
        )
        mock_session.get.return_value = mock_job
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        mock_execute.return_value = {"files_processed": 0}

        result = await run_ingestion_job(job_id)

        # Should handle gracefully
        assert "success" in result

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    async def test_very_large_config(self, mock_execute, mock_get_session, mock_dbos):
        """Test handling of very large configuration"""
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Create large config with many files
        large_config = {
            "source": "s3",
            "files": [f"file_{i}.pdf" for i in range(10000)],
        }

        mock_job = IngestionJob(
            id=uuid.UUID(job_id),
            config=large_config,
            status=JobStatus.PENDING,
        )
        mock_session.get.return_value = mock_job
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        mock_execute.return_value = {"files_processed": 10000}

        result = await run_ingestion_job(job_id)

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    async def test_send_event_with_empty_topic(self, mock_dbos):
        """Test sending event with empty topic"""
        mock_dbos.send_async = AsyncMock()

        await send_completion_event("", "job-123", "SUCCEEDED", {})

        # Should not call send_async with empty topic
        mock_dbos.send_async.assert_not_called()

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    async def test_send_event_with_none_result(self, mock_dbos):
        """Test sending event with None result summary"""
        mock_dbos.send_async = AsyncMock()

        await send_completion_event("topic", "job-123", "FAILED", None)

        mock_dbos.send_async.assert_called_once()
        call_args = mock_dbos.send_async.call_args
        assert call_args[1]["message"]["result_summary"] is None


class TestConcurrencyAndRaceConditions:
    """Tests for concurrency issues and race conditions"""

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    async def test_concurrent_status_updates(self, mock_execute, mock_get_session, mock_dbos):
        """Test that concurrent status updates are handled correctly"""
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_job = IngestionJob(
            id=uuid.UUID(job_id),
            config={"source": "s3"},
            status=JobStatus.PENDING,
        )
        mock_session.get.return_value = mock_job

        # Track commits
        commits = []

        def track_commit():
            commits.append(mock_job.status)

        mock_session.commit = MagicMock(side_effect=track_commit)
        mock_session.refresh = MagicMock()

        mock_execute.return_value = {"files_processed": 10}

        result = await run_ingestion_job(job_id)

        # Verify status transitions happened in order
        assert JobStatus.RUNNING in commits
        assert commits[-1] == JobStatus.SUCCEEDED

    @pytest.mark.asyncio
    @patch("ingestion_service.workflows.DBOS")
    @patch("ingestion_service.workflows.get_session")
    async def test_job_already_running(self, mock_get_session, mock_dbos):
        """Test handling of job that's already running (duplicate workflow start)"""
        job_id = str(uuid.uuid4())
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Job is already RUNNING
        mock_job = IngestionJob(
            id=uuid.UUID(job_id),
            config={"source": "s3"},
            status=JobStatus.RUNNING,
        )
        mock_session.get.return_value = mock_job

        # This could happen if workflow is started twice
        # Implementation should handle gracefully
        result = await run_ingestion_job(job_id)

        # Should either succeed or fail gracefully
        assert "success" in result

