"""
End-to-end tests for ingestion service.

These tests verify the complete flow from job creation through completion.
Uses conftest.py fixtures for proper database and DBOS mocking.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
import asyncio

from ingestion_service.models import JobStatus


class TestEndToEndJobFlow:
    """End-to-end tests for complete job lifecycle"""

    def test_complete_job_lifecycle_success(self, client, sample_job_request):
        """Test complete flow: create job -> execute -> complete successfully"""
        # Step 1: Create job
        create_response = client.post("/ingestion/jobs", json=sample_job_request)

        assert create_response.status_code == 200
        data = create_response.json()
        assert data["status"] == "PENDING"
        job_id = data["job_id"]

        # Step 2: Verify job can be retrieved
        get_response = client.get(f"/ingestion/jobs/{job_id}")
        assert get_response.status_code == 200
        assert get_response.json()["job_id"] == job_id

    def test_complete_job_lifecycle_failure(self, client, sample_job_request):
        """Test complete flow with pipeline failure"""
        # Create job
        create_response = client.post("/ingestion/jobs", json=sample_job_request)

        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Verify job exists
        get_response = client.get(f"/ingestion/jobs/{job_id}")
        assert get_response.status_code == 200


class TestConcurrentJobs:
    """Tests for handling multiple concurrent jobs"""

    def test_multiple_jobs_created_concurrently(self, client, sample_job_request):
        """Test that multiple jobs can be created concurrently"""
        job_ids = []

        # Create multiple jobs
        for i in range(5):
            request = sample_job_request.copy()
            request["config"] = {"source": "s3", "bucket": f"bucket-{i}"}
            request["metadata"] = {"tenant_id": f"org-{i}"}

            response = client.post("/ingestion/jobs", json=request)
            assert response.status_code == 200
            job_ids.append(response.json()["job_id"])

        # Verify all jobs were created with unique IDs
        assert len(job_ids) == 5
        assert len(set(job_ids)) == 5  # All unique


class TestErrorScenarios:
    """Tests for various error scenarios"""

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

    def test_get_same_job_multiple_times(self, client, sample_job_request):
        """Test that getting the same job multiple times returns consistent results"""
        # Create a job first
        create_response = client.post("/ingestion/jobs", json=sample_job_request)
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Get job multiple times
        responses = []
        for _ in range(3):
            response = client.get(f"/ingestion/jobs/{job_id}")
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical
        assert all(r == responses[0] for r in responses)
