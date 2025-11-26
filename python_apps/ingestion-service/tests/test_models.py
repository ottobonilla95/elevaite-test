"""
Tests for ingestion service data models
"""

import pytest
import uuid
from datetime import datetime, timezone

from ingestion_service.models import (
    IngestionJob,
    JobStatus,
    CreateJobRequest,
    JobResponse,
)


class TestJobStatus:
    """Tests for JobStatus enum"""

    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined"""
        assert JobStatus.PENDING == "PENDING"
        assert JobStatus.RUNNING == "RUNNING"
        assert JobStatus.SUCCEEDED == "SUCCEEDED"
        assert JobStatus.FAILED == "FAILED"

    def test_status_values_are_strings(self):
        """Test that status values are strings"""
        for status in JobStatus:
            assert isinstance(status.value, str)


class TestIngestionJob:
    """Tests for IngestionJob model"""

    def test_create_minimal_job(self):
        """Test creating a job with minimal required fields"""
        job = IngestionJob(
            id=uuid.uuid4(),
            config={"source": "s3"},
            status=JobStatus.PENDING,
        )

        assert job.id is not None
        assert job.config == {"source": "s3"}
        assert job.status == JobStatus.PENDING
        assert job.error_message is None
        assert job.callback_topic is None
        assert job.tenant_id is None

    def test_create_full_job(self):
        """Test creating a job with all fields"""
        job_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        job = IngestionJob(
            id=job_id,
            config={"source": "s3", "bucket": "test"},
            status=JobStatus.RUNNING,
            error_message=None,
            callback_topic="wf:exec:step:done",
            tenant_id="org-123",
            execution_id="exec-456",
            step_id="step-789",
            job_type="document_ingestion",
            result_summary={"files_processed": 10},
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

        assert job.id == job_id
        assert job.config["bucket"] == "test"
        assert job.status == JobStatus.RUNNING
        assert job.callback_topic == "wf:exec:step:done"
        assert job.tenant_id == "org-123"
        assert job.execution_id == "exec-456"
        assert job.step_id == "step-789"
        assert job.job_type == "document_ingestion"
        assert job.result_summary["files_processed"] == 10

    def test_status_transitions(self):
        """Test valid status transitions"""
        job = IngestionJob(
            id=uuid.uuid4(),
            config={},
            status=JobStatus.PENDING,
        )

        # PENDING -> RUNNING
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING

        # RUNNING -> SUCCEEDED
        job.status = JobStatus.SUCCEEDED
        assert job.status == JobStatus.SUCCEEDED

    def test_failed_status_with_error(self):
        """Test that failed jobs can have error messages"""
        job = IngestionJob(
            id=uuid.uuid4(),
            config={},
            status=JobStatus.FAILED,
            error_message="Pipeline execution failed",
        )

        assert job.status == JobStatus.FAILED
        assert job.error_message == "Pipeline execution failed"

    def test_completed_job_has_timestamp(self):
        """Test that completed jobs have completion timestamp"""
        now = datetime.now(timezone.utc)
        job = IngestionJob(
            id=uuid.uuid4(),
            config={},
            status=JobStatus.SUCCEEDED,
            completed_at=now,
        )

        assert job.completed_at == now


class TestCreateJobRequest:
    """Tests for CreateJobRequest model"""

    def test_create_request_minimal(self):
        """Test creating request with minimal fields"""
        request = CreateJobRequest(
            config={"source": "s3"},
        )

        assert request.config == {"source": "s3"}
        assert request.metadata is None

    def test_create_request_with_metadata(self):
        """Test creating request with metadata"""
        request = CreateJobRequest(
            config={"source": "s3", "bucket": "test"},
            metadata={
                "tenant_id": "org-123",
                "execution_id": "exec-456",
                "step_id": "step-789",
                "callback_topic": "wf:exec:step:done",
            },
        )

        assert request.config["bucket"] == "test"
        assert request.metadata["tenant_id"] == "org-123"
        assert request.metadata["execution_id"] == "exec-456"
        assert request.metadata["step_id"] == "step-789"
        assert request.metadata["callback_topic"] == "wf:exec:step:done"

    def test_config_can_be_complex(self):
        """Test that config can contain nested structures"""
        request = CreateJobRequest(
            config={
                "source": "s3",
                "bucket": "test",
                "files": ["doc1.pdf", "doc2.pdf"],
                "processing": {
                    "chunk_size": 1000,
                    "overlap": 200,
                },
            },
        )

        assert len(request.config["files"]) == 2
        assert request.config["processing"]["chunk_size"] == 1000


class TestJobResponse:
    """Tests for JobResponse model"""

    def test_response_from_job(self):
        """Test creating response from job"""
        job_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        job = IngestionJob(
            id=job_id,
            config={"source": "s3"},
            status=JobStatus.SUCCEEDED,
            result_summary={"files_processed": 10},
            created_at=now,
            completed_at=now,
        )

        response = JobResponse(
            job_id=job.id,
            status=job.status,
            result_summary=job.result_summary,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )

        assert response.job_id == job_id
        assert response.status == JobStatus.SUCCEEDED
        assert response.result_summary["files_processed"] == 10
        assert response.created_at == now
        assert response.completed_at == now

    def test_response_for_failed_job(self):
        """Test response for failed job includes error"""
        job_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        response = JobResponse(
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message="Pipeline error",
            created_at=now,
        )

        assert response.status == JobStatus.FAILED
        assert response.error_message == "Pipeline error"
        assert response.result_summary is None
