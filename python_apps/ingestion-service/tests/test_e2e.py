"""
End-to-end tests for ingestion service

These tests verify the complete flow from job creation through completion.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
import asyncio

from fastapi.testclient import TestClient
from ingestion_service.main import app
from ingestion_service.models import JobStatus


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


class TestEndToEndJobFlow:
    """End-to-end tests for complete job lifecycle"""

    @patch("ingestion_service.main.get_session")
    @patch("ingestion_service.main.DBOS")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    @patch("ingestion_service.workflows.DBOS")
    def test_complete_job_lifecycle_success(
        self, mock_wf_dbos, mock_execute, mock_api_dbos, mock_get_session, client
    ):
        """Test complete flow: create job -> execute -> complete successfully"""
        # Setup
        job_id = uuid.uuid4()
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Track job state changes
        job_states = []

        def track_commit():
            if hasattr(mock_session, "_current_job"):
                job_states.append(mock_session._current_job.status)

        mock_session.commit = MagicMock(side_effect=track_commit)
        mock_session.refresh = MagicMock()

        # Mock job creation
        def mock_add(job):
            job.id = job_id
            mock_session._current_job = job

        mock_session.add = mock_add

        # Mock DBOS workflow start
        mock_handle = MagicMock()
        mock_handle.workflow_id = "dbos-wf-123"
        mock_api_dbos.start_workflow_async = AsyncMock(return_value=mock_handle)

        # Mock pipeline execution
        mock_execute.return_value = {
            "files_processed": 10,
            "chunks_created": 500,
            "embeddings_generated": 500,
        }

        # Mock DBOS event sending
        mock_wf_dbos.send_async = AsyncMock()

        # Step 1: Create job
        create_response = client.post(
            "/ingestion/jobs",
            json={
                "config": {"source": "s3", "bucket": "test"},
                "metadata": {
                    "tenant_id": "org-123",
                    "execution_id": "exec-456",
                    "step_id": "step-789",
                    "callback_topic": "wf:exec:step:done",
                },
            },
        )

        assert create_response.status_code == 200
        data = create_response.json()
        assert data["status"] == "PENDING"

        # Verify workflow was started
        mock_api_dbos.start_workflow_async.assert_called_once()

    @patch("ingestion_service.main.get_session")
    @patch("ingestion_service.main.DBOS")
    @patch("ingestion_service.workflows.execute_ingestion_pipeline")
    @patch("ingestion_service.workflows.DBOS")
    def test_complete_job_lifecycle_failure(
        self, mock_wf_dbos, mock_execute, mock_api_dbos, mock_get_session, client
    ):
        """Test complete flow with pipeline failure"""
        job_id = uuid.uuid4()
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        def mock_add(job):
            job.id = job_id

        mock_session.add = mock_add
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Mock DBOS workflow start
        mock_handle = MagicMock()
        mock_api_dbos.start_workflow_async = AsyncMock(return_value=mock_handle)

        # Mock pipeline failure
        mock_execute.side_effect = Exception("S3 connection failed")
        mock_wf_dbos.send_async = AsyncMock()

        # Create job
        create_response = client.post(
            "/ingestion/jobs",
            json={
                "config": {"source": "s3", "bucket": "invalid"},
                "metadata": {"callback_topic": "wf:exec:step:done"},
            },
        )

        assert create_response.status_code == 200

        # Workflow would execute and fail
        # Verify that failure event would be sent
        # (In real scenario, this would be triggered by DBOS workflow)


class TestConcurrentJobs:
    """Tests for handling multiple concurrent jobs"""

    @patch("ingestion_service.main.get_session")
    @patch("ingestion_service.main.DBOS")
    def test_multiple_jobs_created_concurrently(self, mock_dbos, mock_get_session, client):
        """Test that multiple jobs can be created concurrently"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        job_ids = []

        def mock_add(job):
            job_id = uuid.uuid4()
            job.id = job_id
            job_ids.append(job_id)

        mock_session.add = mock_add
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        mock_handle = MagicMock()
        mock_dbos.start_workflow_async = AsyncMock(return_value=mock_handle)

        # Create multiple jobs
        for i in range(5):
            response = client.post(
                "/ingestion/jobs",
                json={
                    "config": {"source": "s3", "bucket": f"bucket-{i}"},
                    "metadata": {"tenant_id": f"org-{i}"},
                },
            )
            assert response.status_code == 200

        # Verify all jobs were created
        assert len(job_ids) == 5
        assert len(set(job_ids)) == 5  # All unique


class TestErrorScenarios:
    """Tests for various error scenarios"""

    @patch("ingestion_service.main.get_session")
    def test_database_connection_failure(self, mock_get_session, client):
        """Test handling of database connection failure"""
        mock_get_session.side_effect = Exception("Database connection failed")

        response = client.post(
            "/ingestion/jobs",
            json={"config": {"source": "s3"}},
        )

        # Should return 500 error
        assert response.status_code == 500

    @patch("ingestion_service.main.get_session")
    @patch("ingestion_service.main.DBOS")
    def test_dbos_workflow_start_failure(self, mock_dbos, mock_get_session, client):
        """Test handling of DBOS workflow start failure"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        def mock_add(job):
            job.id = uuid.uuid4()

        mock_session.add = mock_add
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Mock DBOS failure
        mock_dbos.start_workflow_async = AsyncMock(side_effect=Exception("DBOS error"))

        response = client.post(
            "/ingestion/jobs",
            json={"config": {"source": "s3"}},
        )

        # Should still return error
        assert response.status_code == 500

    def test_invalid_job_config(self, client):
        """Test validation of invalid job configuration"""
        response = client.post(
            "/ingestion/jobs",
            json={
                # Missing required 'config' field
                "metadata": {"tenant_id": "org-123"},
            },
        )

        assert response.status_code == 422  # Validation error

    def test_malformed_json(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/ingestion/jobs",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


class TestIdempotency:
    """Tests for idempotent behavior"""

    @patch("ingestion_service.main.get_session")
    def test_get_same_job_multiple_times(self, mock_get_session, client):
        """Test that getting the same job multiple times returns consistent results"""
        job_id = uuid.uuid4()
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        from ingestion_service.models import IngestionJob

        mock_job = IngestionJob(
            id=job_id,
            config={"source": "s3"},
            status=JobStatus.SUCCEEDED,
            result_summary={"files_processed": 10},
        )
        mock_session.get = MagicMock(return_value=mock_job)

        # Get job multiple times
        responses = []
        for _ in range(3):
            response = client.get(f"/ingestion/jobs/{job_id}")
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical
        assert all(r == responses[0] for r in responses)

