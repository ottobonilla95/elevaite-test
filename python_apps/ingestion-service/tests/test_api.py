"""
Tests for ingestion service API endpoints
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
from fastapi.testclient import TestClient

from ingestion_service.main import app
from ingestion_service.models import IngestionJob, JobStatus


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create a mock database session"""
    session = MagicMock()
    return session


class TestCreateIngestionJob:
    """Tests for POST /ingestion/jobs"""

    @patch("ingestion_service.main.get_session")
    @patch("ingestion_service.main.DBOS")
    def test_create_job_success(self, mock_dbos, mock_get_session, client, mock_session):
        """Test successful job creation"""
        mock_get_session.return_value = mock_session

        # Mock DBOS workflow start
        mock_handle = MagicMock()
        mock_handle.workflow_id = "dbos-wf-123"
        mock_dbos.start_workflow_async = AsyncMock(return_value=mock_handle)

        # Mock database operations
        job_id = uuid.uuid4()
        mock_job = IngestionJob(
            id=job_id,
            config={"source": "s3"},
            status=JobStatus.PENDING,
        )

        def mock_add(job):
            job.id = job_id

        mock_session.add = mock_add
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Make request
        response = client.post(
            "/ingestion/jobs",
            json={
                "config": {"source": "s3", "bucket": "test-bucket"},
                "metadata": {
                    "tenant_id": "org-123",
                    "execution_id": "exec-456",
                    "step_id": "ingestion-step",
                    "callback_topic": "wf:exec:step:ingestion_done",
                },
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "PENDING"

    @patch("ingestion_service.main.get_session")
    def test_create_job_validation_error(self, mock_get_session, client, mock_session):
        """Test job creation with invalid config"""
        mock_get_session.return_value = mock_session

        # Make request with missing config
        response = client.post(
            "/ingestion/jobs",
            json={
                "metadata": {"tenant_id": "org-123"},
            },
        )

        # Verify error response
        assert response.status_code == 422  # Validation error


class TestGetIngestionJob:
    """Tests for GET /ingestion/jobs/{job_id}"""

    @patch("ingestion_service.main.get_session")
    def test_get_job_success(self, mock_get_session, client, mock_session):
        """Test successful job retrieval"""
        mock_get_session.return_value = mock_session

        # Mock database query
        job_id = uuid.uuid4()
        mock_job = IngestionJob(
            id=job_id,
            config={"source": "s3"},
            status=JobStatus.SUCCEEDED,
            result_summary={"files_processed": 10},
        )
        mock_session.get = MagicMock(return_value=mock_job)

        # Make request
        response = client.get(f"/ingestion/jobs/{job_id}")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(job_id)
        assert data["status"] == "SUCCEEDED"
        assert data["result_summary"]["files_processed"] == 10

    @patch("ingestion_service.main.get_session")
    def test_get_job_not_found(self, mock_get_session, client, mock_session):
        """Test job retrieval when job doesn't exist"""
        mock_get_session.return_value = mock_session

        # Mock database query returning None
        job_id = uuid.uuid4()
        mock_session.get = MagicMock(return_value=None)

        # Make request
        response = client.get(f"/ingestion/jobs/{job_id}")

        # Verify error response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestHealthCheck:
    """Tests for GET /health"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

