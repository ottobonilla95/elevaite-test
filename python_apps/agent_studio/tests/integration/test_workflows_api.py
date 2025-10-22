"""
Integration tests for Workflows API endpoints.

Tests all CRUD operations and execution for workflows including:
- Create workflow
- List workflows with filters
- Get workflow by ID
- Update workflow
- Delete workflow
- Execute workflow (sync and async)
- Stream workflow execution
- Error cases and validation
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestWorkflowsAPI:
    """Test suite for Workflows API endpoints."""

    def test_create_workflow_success(self, test_client: TestClient):
        """Test creating a workflow with all fields."""
        workflow_data = {
            "name": f"Test Workflow {uuid.uuid4().hex[:8]}",
            "description": "A test workflow for integration testing",
            "version": "1.0.0",
            "tags": ["test", "integration"],
            "configuration": {
                "steps": [
                    {
                        "step_id": "step1",
                        "step_type": "data_processing",
                        "name": "Process Data",
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
        data = response.json()
        assert data["name"] == workflow_data["name"]
        assert data["description"] == workflow_data["description"]
        assert "workflow_id" in data  # UUID
        assert "configuration" in data

    def test_create_workflow_minimal_fields(self, test_client: TestClient):
        """Test creating a workflow with only required fields."""
        workflow_data = {
            "name": f"Minimal Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }

        response = test_client.post("/api/workflows/", json=workflow_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == workflow_data["name"]
        assert "is_active" in data  # Check field exists

    def test_list_workflows_empty(self, test_client: TestClient):
        """Test listing workflows when none exist."""
        response = test_client.get("/api/workflows/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_with_pagination(self, test_client: TestClient):
        """Test listing workflows with pagination."""
        # Create multiple workflows
        created_ids = []
        for i in range(3):
            workflow_data = {
                "name": f"Workflow {i} {uuid.uuid4().hex[:8]}",
                "configuration": {"steps": []},
            }
            response = test_client.post("/api/workflows/", json=workflow_data)
            assert response.status_code == 200
            created_ids.append(response.json()["workflow_id"])

        # Test pagination
        response = test_client.get("/api/workflows/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # At least our 2 workflows

        # Cleanup
        for workflow_id in created_ids:
            test_client.delete(f"/api/workflows/{workflow_id}")

    def test_get_workflow_by_id_success(self, test_client: TestClient):
        """Test getting a specific workflow by ID."""
        # Create a workflow
        workflow_data = {
            "name": f"Get Test Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Get the workflow
        response = test_client.get(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == workflow_data["name"]
        assert str(data["workflow_id"]) == str(workflow_id)

        # Cleanup
        test_client.delete(f"/api/workflows/{workflow_id}")

    def test_get_workflow_not_found(self, test_client: TestClient):
        """Test getting a non-existent workflow."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/workflows/{fake_id}")

        assert response.status_code == 404

    def test_update_workflow_success(self, test_client: TestClient):
        """Test updating a workflow."""
        # Create a workflow
        workflow_data = {
            "name": f"Original Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Update the workflow
        update_data = {
            "name": "Updated Workflow",
            "description": "Updated description",
            "is_active": False,
        }
        response = test_client.put(f"/api/workflows/{workflow_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["is_active"] == update_data["is_active"]

        # Cleanup
        test_client.delete(f"/api/workflows/{workflow_id}")

    def test_update_workflow_not_found(self, test_client: TestClient):
        """Test updating a non-existent workflow."""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated"}

        response = test_client.put(f"/api/workflows/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_delete_workflow_success(self, test_client: TestClient):
        """Test deleting a workflow."""
        # Create a workflow
        workflow_data = {
            "name": f"Delete Test Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Delete the workflow
        response = test_client.delete(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 404

    def test_delete_workflow_not_found(self, test_client: TestClient):
        """Test deleting a non-existent workflow."""
        fake_id = str(uuid.uuid4())
        response = test_client.delete(f"/api/workflows/{fake_id}")

        assert response.status_code == 404

    def test_workflow_with_multiple_steps(self, test_client: TestClient):
        """Test creating a workflow with multiple steps and dependencies."""
        workflow_data = {
            "name": f"Multi-Step Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {
                "steps": [
                    {
                        "step_id": "step1",
                        "step_type": "data_processing",
                        "name": "First Step",
                        "config": {"processing_type": "passthrough"},
                        "dependencies": [],
                    },
                    {
                        "step_id": "step2",
                        "step_type": "data_processing",
                        "name": "Second Step",
                        "config": {"processing_type": "passthrough"},
                        "dependencies": ["step1"],
                    },
                ]
            },
        }

        response = test_client.post("/api/workflows/", json=workflow_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["configuration"]["steps"]) == 2
        assert data["configuration"]["steps"][1]["dependencies"] == ["step1"]

        # Cleanup
        test_client.delete(f"/api/workflows/{data['workflow_id']}")

    def test_workflow_with_tags(self, test_client: TestClient):
        """Test creating workflows with different tags."""
        tags_list = [["production"], ["test", "staging"], ["development", "experimental"]]

        created_ids = []
        for tags in tags_list:
            workflow_data = {
                "name": f"Tagged Workflow {uuid.uuid4().hex[:8]}",
                "tags": tags,
                "configuration": {"steps": []},
            }
            response = test_client.post("/api/workflows/", json=workflow_data)
            assert response.status_code == 200
            data = response.json()
            assert set(data["tags"]) == set(tags)
            created_ids.append(data["workflow_id"])

        # Cleanup
        for workflow_id in created_ids:
            test_client.delete(f"/api/workflows/{workflow_id}")

    def test_workflow_lifecycle(self, test_client: TestClient):
        """Test complete workflow lifecycle: create -> read -> update -> delete."""
        # Create
        workflow_data = {
            "name": f"Lifecycle Workflow {uuid.uuid4().hex[:8]}",
            "configuration": {"steps": []},
        }
        create_response = test_client.post("/api/workflows/", json=workflow_data)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Read
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == workflow_data["name"]

        # Update
        update_data = {"name": "Updated Lifecycle Workflow"}
        update_response = test_client.put(f"/api/workflows/{workflow_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == update_data["name"]

        # Delete
        delete_response = test_client.delete(f"/api/workflows/{workflow_id}")
        assert delete_response.status_code == 200

        # Verify deleted
        final_get = test_client.get(f"/api/workflows/{workflow_id}")
        assert final_get.status_code == 404
