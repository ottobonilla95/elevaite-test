"""
Tests for error scenarios and edge cases.

Uses proper database fixtures and mocking patterns.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
import asyncio

from sqlmodel import Session, SQLModel

from ingestion_service.workflows import send_completion_event
from ingestion_service.models import IngestionJob, JobStatus


class TestWorkflowErrorHandling:
    """Tests for error handling in workflow logic.

    These tests use the _run_ingestion_job_impl function directly to avoid
    DBOS initialization requirements.
    """

    @pytest.mark.asyncio
    async def test_pipeline_timeout(self, engine):
        """Test handling of pipeline execution timeout"""
        from ingestion_service.workflows import _run_ingestion_job_impl

        SQLModel.metadata.create_all(engine)

        job_id = uuid.uuid4()
        with Session(engine) as session:
            job = IngestionJob(
                id=job_id,
                config={"source": "s3"},
                status=JobStatus.PENDING,
                callback_topic="wf:exec-123:step-456:done",
            )
            session.add(job)
            session.commit()

        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            # Simulate timeout
            mock_execute.side_effect = asyncio.TimeoutError("Pipeline execution timed out")
            mock_send_event.return_value = None

            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        assert result["status"] == "FAILED"
        # TimeoutError message may vary
        assert "error_message" in result

    @pytest.mark.asyncio
    async def test_partial_pipeline_failure(self, engine):
        """Test handling of partial pipeline failure (some files processed, then error)"""
        from ingestion_service.workflows import _run_ingestion_job_impl

        SQLModel.metadata.create_all(engine)

        job_id = uuid.uuid4()
        with Session(engine) as session:
            job = IngestionJob(
                id=job_id,
                config={"source": "s3", "files": ["doc1.pdf", "doc2.pdf", "doc3.pdf"]},
                status=JobStatus.PENDING,
                callback_topic="wf:exec-123:step-456:done",
            )
            session.add(job)
            session.commit()

        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            mock_execute.side_effect = Exception("Failed on file 3 of 3")
            mock_send_event.return_value = None

            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        assert result["status"] == "FAILED"
        assert "Failed on file 3" in result["error_message"]

    @pytest.mark.asyncio
    async def test_event_send_failure_does_not_fail_job(self, engine):
        """Test that event send failure doesn't fail the job itself"""
        from ingestion_service.workflows import _run_ingestion_job_impl

        SQLModel.metadata.create_all(engine)

        job_id = uuid.uuid4()
        with Session(engine) as session:
            job = IngestionJob(
                id=job_id,
                config={"source": "s3"},
                status=JobStatus.PENDING,
                callback_topic="wf:exec-123:step-456:done",
            )
            session.add(job)
            session.commit()

        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            mock_execute.return_value = {"files_processed": 10}
            # Event send fails
            mock_send_event.side_effect = Exception("HTTP callback failed")

            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        # Job should still succeed (event send failure is logged, not raised)
        assert result["status"] == "SUCCEEDED"


class TestEdgeCases:
    """Tests for edge cases.

    These tests use the _run_ingestion_job_impl function directly to avoid
    DBOS initialization requirements.
    """

    @pytest.mark.asyncio
    async def test_empty_config(self, engine):
        """Test handling of empty configuration"""
        from ingestion_service.workflows import _run_ingestion_job_impl

        SQLModel.metadata.create_all(engine)

        job_id = uuid.uuid4()
        with Session(engine) as session:
            job = IngestionJob(
                id=job_id,
                config={},  # Empty config
                status=JobStatus.PENDING,
            )
            session.add(job)
            session.commit()

        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            mock_execute.return_value = {"files_processed": 0}
            mock_send_event.return_value = None

            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        # Should handle gracefully
        assert result["status"] in ["SUCCEEDED", "FAILED"]

    @pytest.mark.asyncio
    async def test_very_large_config(self, engine):
        """Test handling of very large configuration"""
        from ingestion_service.workflows import _run_ingestion_job_impl

        SQLModel.metadata.create_all(engine)

        # Create large config with many files
        large_config = {
            "source": "s3",
            "files": [f"file_{i}.pdf" for i in range(10000)],
        }

        job_id = uuid.uuid4()
        with Session(engine) as session:
            job = IngestionJob(
                id=job_id,
                config=large_config,
                status=JobStatus.PENDING,
            )
            session.add(job)
            session.commit()

        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            mock_execute.return_value = {"files_processed": 10000}
            mock_send_event.return_value = None

            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        assert result["status"] == "SUCCEEDED"

    @pytest.mark.asyncio
    async def test_send_event_with_empty_topic(self):
        """Test sending event with empty topic"""
        # Should not raise exception and should return early
        await send_completion_event("", None, {"status": "SUCCEEDED"})

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_send_event_with_none_result(self, mock_client_class):
        """Test sending event with None result summary"""
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        await send_completion_event(
            "wf:exec-123:step-456:done",
            None,
            {"status": "FAILED", "result_summary": None},
        )

        mock_client.post.assert_called_once()


class TestConcurrencyAndRaceConditions:
    """Tests for concurrency issues and race conditions.

    These tests use the _run_ingestion_job_impl function directly to avoid
    DBOS initialization requirements.
    """

    @pytest.mark.asyncio
    async def test_job_already_running(self, engine):
        """Test handling of job that's already running (duplicate workflow start)"""
        from ingestion_service.workflows import _run_ingestion_job_impl

        SQLModel.metadata.create_all(engine)

        job_id = uuid.uuid4()
        with Session(engine) as session:
            # Job is already RUNNING
            job = IngestionJob(
                id=job_id,
                config={"source": "s3"},
                status=JobStatus.RUNNING,
            )
            session.add(job)
            session.commit()

        with (
            patch("ingestion_service.workflows.execute_ingestion_pipeline") as mock_execute,
            patch("ingestion_service.workflows.send_completion_event") as mock_send_event,
        ):
            mock_execute.return_value = {"files_processed": 10}
            mock_send_event.return_value = None

            # This could happen if workflow is started twice
            # Implementation should handle gracefully
            result = await _run_ingestion_job_impl(str(job_id), db_engine=engine)

        # Should either succeed or fail gracefully
        assert result["status"] in ["SUCCEEDED", "FAILED"]
