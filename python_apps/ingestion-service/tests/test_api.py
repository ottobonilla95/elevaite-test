"""
Tests for ingestion service API endpoints.

Uses conftest.py fixtures for proper database and DBOS mocking.
"""

import pytest
import uuid

from ingestion_service.models import IngestionJob, JobStatus


class TestCreateIngestionJob:
    """Tests for POST /ingestion/jobs"""

    def test_create_job_success(self, client, sample_job_request):
        """Test successful job creation"""
        response = client.post("/ingestion/jobs", json=sample_job_request)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "PENDING"

    def test_create_job_validation_error(self, client):
        """Test job creation with invalid config"""
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

    def test_get_job_success(self, client, sample_job_request):
        """Test successful job retrieval"""
        # First create a job
        create_response = client.post("/ingestion/jobs", json=sample_job_request)
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Now retrieve it
        response = client.get(f"/ingestion/jobs/{job_id}")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "PENDING"

    def test_get_job_not_found(self, client):
        """Test job retrieval when job doesn't exist"""
        job_id = uuid.uuid4()

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
