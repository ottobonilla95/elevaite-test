"""
Smoke tests for pipeline endpoints.

These tests ensure the pipeline endpoints are not broken and can handle
basic requests. Full integration tests will be implemented when the pipeline
system is properly integrated into the new API architecture.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.unit
class TestPipelineEndpoints:
    """Test pipeline API endpoints."""

    def test_get_pipeline_config_template(self, test_client: TestClient):
        """Test getting pipeline configuration template."""
        response = test_client.get("/api/pipeline/config/template")

        assert response.status_code == 200
        data = response.json()

        # Verify template structure
        assert "steps" in data
        assert "file_id" in data
        assert "pipeline_name" in data

        # Verify steps
        assert len(data["steps"]) == 5
        step_types = [step["step_type"] for step in data["steps"]]
        assert step_types == ["load", "parse", "chunk", "embed", "store"]

        # Verify each step has config
        for step in data["steps"]:
            assert "config" in step
            assert isinstance(step["config"], dict)

    def test_get_pipeline_status_not_found(self, test_client: TestClient):
        """Test getting status of non-existent pipeline."""
        response = test_client.get("/api/pipeline/nonexistent-pipeline-id/status")

        assert response.status_code == 200
        data = response.json()

        assert data["pipeline_id"] == "nonexistent-pipeline-id"
        assert data["status"] == "not_found"
        assert data["message"] == "Pipeline not found"

    @patch("api.pipeline_endpoints.pipeline_executor")
    def test_execute_pipeline_missing_steps(self, mock_executor, test_client: TestClient):
        """Test pipeline execution with missing steps."""
        request_data = {
            "steps": [],
            "file_id": "test-file-id",
            "pipeline_name": "test-pipeline",
        }

        response = test_client.post("/api/pipeline/execute", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "No pipeline steps provided" in data["detail"]

    @patch("api.pipeline_endpoints.pipeline_executor")
    def test_execute_pipeline_missing_files(self, mock_executor, test_client: TestClient):
        """Test pipeline execution with missing files."""
        request_data = {
            "steps": [
                {"step_type": "load", "config": {}},
                {"step_type": "parse", "config": {}},
            ],
            "pipeline_name": "test-pipeline",
        }

        response = test_client.post("/api/pipeline/execute", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "No files provided for processing" in data["detail"]

    @patch("api.pipeline_endpoints.pipeline_executor")
    def test_execute_pipeline_success(self, mock_executor, test_client: TestClient):
        """Test successful pipeline execution request."""
        request_data = {
            "steps": [
                {"step_type": "load", "config": {"provider": "local"}},
                {"step_type": "parse", "config": {"provider": "unstructured"}},
                {"step_type": "chunk", "config": {"strategy": "recursive"}},
                {"step_type": "embed", "config": {"provider": "openai"}},
                {"step_type": "store", "config": {"provider": "qdrant"}},
            ],
            "file_id": "test-file-id",
            "pipeline_name": "test-pipeline",
        }

        response = test_client.post("/api/pipeline/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "pipeline_id" in data
        assert data["status"] == "running"
        assert data["steps_completed"] == 0
        assert data["total_steps"] == 5
        assert "Pipeline started successfully" in data["message"]

    @patch("api.pipeline_endpoints.pipeline_executor")
    def test_execute_pipeline_with_multiple_files(self, mock_executor, test_client: TestClient):
        """Test pipeline execution with multiple files."""
        request_data = {
            "steps": [
                {"step_type": "load", "config": {}},
                {"step_type": "parse", "config": {}},
            ],
            "file_ids": ["file-1", "file-2", "file-3"],
            "pipeline_name": "multi-file-pipeline",
        }

        response = test_client.post("/api/pipeline/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["total_steps"] == 2

    @patch("api.pipeline_endpoints.pipeline_executor")
    def test_execute_pipeline_with_custom_pipeline_id(self, mock_executor, test_client: TestClient):
        """Test pipeline execution with custom pipeline ID."""
        custom_id = "my-custom-pipeline-id"
        request_data = {
            "steps": [{"step_type": "load", "config": {}}],
            "file_id": "test-file-id",
            "pipeline_id": custom_id,
        }

        response = test_client.post("/api/pipeline/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_id"] == custom_id

    def test_stream_pipeline_progress_not_found(self, test_client: TestClient):
        """Test streaming progress for non-existent pipeline."""
        response = test_client.get(
            "/api/pipeline/progress/nonexistent-pipeline-id",
            headers={"Accept": "text/event-stream"},
        )

        # Should return 404 for non-existent pipeline
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
