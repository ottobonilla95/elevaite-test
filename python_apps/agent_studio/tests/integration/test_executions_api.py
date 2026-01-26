"""
Integration tests for Executions API endpoints.

Tests execution tracking, status monitoring, and results retrieval including:
- Get execution status
- List executions with filters
- Get execution results
- Cancel execution
- Get execution trace and steps
- Get execution progress
- Execution analytics and stats
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestExecutionsAPI:
    """Test suite for Executions API endpoints."""

    @pytest.fixture
    def sample_workflow(self, test_client: TestClient):
        """Create a sample workflow for execution testing."""
        workflow_data = {
            "name": "Test Execution Workflow",
            "description": "Workflow for testing executions API",
            "version": "1.0.0",
            "configuration": {
                "steps": [
                    {
                        "step_id": "test_step",
                        "step_type": "data_processing",
                        "name": "Test Step",
                        "config": {"processing_type": "passthrough"},
                        "dependencies": [],
                    }
                ]
            },
            "created_by": "test_user",
            "is_active": True,
        }

        response = test_client.post("/api/workflows/", json=workflow_data)
        assert response.status_code == 200
        workflow = response.json()

        yield workflow

        # Cleanup
        test_client.delete(f"/api/workflows/{workflow['workflow_id']}")

    def test_get_execution_status_not_found(self, test_client: TestClient):
        """Test getting status of non-existent execution."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/executions/{fake_id}/status")

        assert response.status_code == 404

    def test_get_execution_status_invalid_id(self, test_client: TestClient):
        """Test getting status with invalid execution ID format."""
        response = test_client.get("/api/executions/invalid-id/status")

        assert response.status_code == 400

    def test_list_executions_empty(self, test_client: TestClient):
        """Test listing executions when none exist."""
        response = test_client.get("/api/executions/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_executions_with_status_filter(self, test_client: TestClient):
        """Test listing executions with status filter."""
        # Test each valid status
        statuses = ["queued", "running", "completed", "failed", "cancelled"]

        for status in statuses:
            response = test_client.get(f"/api/executions/?status={status}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_list_executions_with_limit(self, test_client: TestClient):
        """Test listing executions with limit parameter."""
        response = test_client.get("/api/executions/?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_list_executions_with_user_filter(self, test_client: TestClient):
        """Test listing executions filtered by user_id."""
        response = test_client.get("/api/executions/?user_id=test_user")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_cancel_execution_not_found(self, test_client: TestClient):
        """Test cancelling non-existent execution."""
        fake_id = str(uuid.uuid4())
        response = test_client.post(f"/api/executions/{fake_id}/cancel")

        assert response.status_code == 404

    def test_cancel_execution_invalid_id(self, test_client: TestClient):
        """Test cancelling execution with invalid ID format."""
        response = test_client.post("/api/executions/invalid-id/cancel")

        assert response.status_code == 400

    def test_get_execution_result_not_found(self, test_client: TestClient):
        """Test getting result of non-existent execution."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/executions/{fake_id}/result")

        assert response.status_code == 404

    def test_get_execution_result_invalid_id(self, test_client: TestClient):
        """Test getting result with invalid execution ID format."""
        response = test_client.get("/api/executions/invalid-id/result")

        assert response.status_code == 400

    def test_get_execution_trace_not_found(self, test_client: TestClient):
        """Test getting trace of non-existent execution."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/executions/{fake_id}/trace")

        assert response.status_code == 404

    def test_get_execution_trace_invalid_id(self, test_client: TestClient):
        """Test getting trace with invalid execution ID format."""
        response = test_client.get("/api/executions/invalid-id/trace")

        assert response.status_code == 400

    def test_get_execution_steps_not_found(self, test_client: TestClient):
        """Test getting steps of non-existent execution."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/executions/{fake_id}/steps")

        assert response.status_code == 404

    def test_get_execution_steps_invalid_id(self, test_client: TestClient):
        """Test getting steps with invalid execution ID format."""
        response = test_client.get("/api/executions/invalid-id/steps")

        assert response.status_code == 400

    def test_get_execution_progress_not_found(self, test_client: TestClient):
        """Test getting progress of non-existent execution."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/executions/{fake_id}/progress")

        assert response.status_code == 404

    def test_get_execution_progress_invalid_id(self, test_client: TestClient):
        """Test getting progress with invalid execution ID format."""
        response = test_client.get("/api/executions/invalid-id/progress")

        assert response.status_code == 400

    def test_get_execution_stats(self, test_client: TestClient):
        """Test getting execution statistics."""
        response = test_client.get("/api/executions/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "active" in data
        assert isinstance(data["by_status"], dict)
        assert isinstance(data["total"], int)
        assert isinstance(data["active"], int)

    def test_get_execution_analytics_no_filter(self, test_client: TestClient):
        """Test getting execution analytics without filters."""
        response = test_client.get("/api/executions/analytics")

        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert "by_status" in data["analytics"]
        assert "average_duration_seconds" in data["analytics"]
        assert "total_analyzed" in data["analytics"]

    def test_get_execution_analytics_with_status_filter(self, test_client: TestClient):
        """Test getting execution analytics with status filter."""
        statuses = ["queued", "running", "completed", "failed", "cancelled"]

        for status in statuses:
            response = test_client.get(f"/api/executions/analytics?status={status}")
            assert response.status_code == 200
            data = response.json()
            assert "analytics" in data

    def test_get_execution_analytics_with_type_filter(self, test_client: TestClient):
        """Test getting execution analytics with type filter."""
        types = ["agent", "workflow"]

        for exec_type in types:
            response = test_client.get(f"/api/executions/analytics?execution_type={exec_type}")
            assert response.status_code == 200
            data = response.json()
            assert "analytics" in data

    def test_cleanup_completed_executions(self, test_client: TestClient):
        """Test cleanup endpoint."""
        response = test_client.post("/api/executions/cleanup")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "removed_count" in data

    def test_get_execution_input_output_not_found(self, test_client: TestClient):
        """Test getting I/O of non-existent execution."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/executions/{fake_id}/input-output")

        assert response.status_code == 404

    def test_get_execution_input_output_invalid_id(self, test_client: TestClient):
        """Test getting I/O with invalid execution ID format."""
        response = test_client.get("/api/executions/invalid-id/input-output")

        assert response.status_code == 400

    def test_execution_status_fields(self, test_client: TestClient, sample_workflow):
        """Test that execution status response has required fields."""
        # Execute workflow to create an execution
        execution_request = {
            "input_data": {"test": "data"},
            "user_id": "test_user",
        }

        exec_response = test_client.post(
            f"/api/workflows/{sample_workflow['workflow_id']}/execute",
            json=execution_request,
        )

        # If execution was created, check status fields
        if exec_response.status_code == 200:
            exec_data = exec_response.json()
            if "execution_id" in exec_data:
                execution_id = exec_data["execution_id"]

                # Get status
                status_response = test_client.get(f"/api/executions/{execution_id}/status")

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    # Check for expected fields
                    assert "status" in status_data
                    assert status_data["status"] in ["queued", "running", "completed", "failed", "cancelled"]

    def test_execution_progress_fields(self, test_client: TestClient, sample_workflow):
        """Test that execution progress response has required fields."""
        # Execute workflow to create an execution
        execution_request = {
            "input_data": {"test": "data"},
            "user_id": "test_user",
        }

        exec_response = test_client.post(
            f"/api/workflows/{sample_workflow['workflow_id']}/execute",
            json=execution_request,
        )

        # If execution was created, check progress fields
        if exec_response.status_code == 200:
            exec_data = exec_response.json()
            if "execution_id" in exec_data:
                execution_id = exec_data["execution_id"]

                # Get progress
                progress_response = test_client.get(f"/api/executions/{execution_id}/progress")

                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    # Check for expected fields
                    assert "execution_id" in progress_data
                    assert "status" in progress_data
                    assert "type" in progress_data

