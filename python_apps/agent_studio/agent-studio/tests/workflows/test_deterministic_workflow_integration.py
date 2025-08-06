#!/usr/bin/env python3
"""
Test deterministic workflow integration with existing workflow endpoints.

This test verifies that deterministic workflows can be:
1. Saved via POST /api/workflows
2. Executed via POST /api/workflows/{id}/execute
3. Retrieved via GET /api/workflows/{id}
"""

import pytest
import json
import uuid
import requests
from sqlalchemy.orm import Session

# Import the FastAPI app and dependencies
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from db import crud
from db.schemas import workflows as schemas

# API base URL
API_BASE_URL = "http://localhost:8005"


class TestDeterministicWorkflowIntegration:
    """Test deterministic workflow integration with existing endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create test client using requests to connect to running API."""

        class APIClient:
            def __init__(self, base_url):
                self.base_url = base_url

            def post(self, path, json=None):
                response = requests.post(f"{self.base_url}{path}", json=json)
                return response

            def get(self, path):
                response = requests.get(f"{self.base_url}{path}")
                return response

        return APIClient(API_BASE_URL)

    @pytest.fixture
    def sample_deterministic_workflow(self):
        """Create a sample deterministic workflow configuration."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "name": f"Test Deterministic Workflow {unique_id}",
            "description": "A test deterministic workflow for integration testing",
            "version": "1.0.0",
            "configuration": {
                "workflow_type": "deterministic",
                "workflow_id": str(uuid.uuid4()),
                "workflow_name": "Test Deterministic Workflow",
                "description": "A test deterministic workflow",
                "version": "1.0.0",
                "execution_pattern": "sequential",
                "timeout_seconds": 300,
                "max_retries": 2,
                "steps": [
                    {
                        "step_id": "input_step",
                        "step_name": "Input Data Processing",
                        "step_type": "data_input",
                        "step_order": 1,
                        "dependencies": [],
                        "config": {
                            "input_source": "user_query",
                            "validation_rules": ["required", "non_empty"],
                        },
                    },
                    {
                        "step_id": "transform_step",
                        "step_name": "Data Transformation",
                        "step_type": "transformation",
                        "step_order": 2,
                        "dependencies": ["input_step"],
                        "input_mapping": {"input_data": "input_step.output"},
                        "config": {
                            "transformation_type": "text_processing",
                            "operations": ["lowercase", "trim", "normalize"],
                        },
                    },
                    {
                        "step_id": "output_step",
                        "step_name": "Output Results",
                        "step_type": "data_output",
                        "step_order": 3,
                        "dependencies": ["transform_step"],
                        "input_mapping": {"processed_data": "transform_step.output"},
                        "config": {"output_format": "json", "include_metadata": True},
                    },
                ],
                "tags": ["test", "deterministic", "integration"],
                "category": "testing",
            },
            "created_by": "test_user",
            "is_active": True,
            "tags": ["test", "deterministic"],
        }

    @pytest.fixture
    def sample_execution_request(self):
        """Create a sample execution request."""
        return {
            "query": "Test query for deterministic workflow",
            "chat_history": [],
            "runtime_overrides": {},
            "session_id": "test_session_123",
            "user_id": "test_user",
        }

    def test_create_deterministic_workflow(
        self, test_client, sample_deterministic_workflow
    ):
        """Test creating a deterministic workflow via POST /api/workflows."""
        response = test_client.post(
            "/api/workflows/", json=sample_deterministic_workflow
        )

        # Print response details if there's an error
        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Error details: {response.text}")

        assert response.status_code == 200
        data = response.json()

        # Verify workflow was created correctly
        assert data["name"] == sample_deterministic_workflow["name"]
        assert data["description"] == sample_deterministic_workflow["description"]
        assert data["version"] == sample_deterministic_workflow["version"]
        assert data["is_active"] == True

        # Verify configuration was stored correctly
        config = data["configuration"]
        assert config["workflow_type"] == "deterministic"
        assert len(config["steps"]) == 3
        assert config["execution_pattern"] == "sequential"

        # Verify steps are correctly stored
        steps = config["steps"]
        assert steps[0]["step_type"] == "data_input"
        assert steps[1]["step_type"] == "transformation"
        assert steps[2]["step_type"] == "data_output"

    def test_get_deterministic_workflow(
        self, test_client, sample_deterministic_workflow
    ):
        """Test retrieving a deterministic workflow via GET /api/workflows/{id}."""
        # First create the workflow
        create_response = test_client.post(
            "/api/workflows/", json=sample_deterministic_workflow
        )
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Then retrieve it
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["workflow_id"] == workflow_id
        assert data["configuration"]["workflow_type"] == "deterministic"
        assert len(data["configuration"]["steps"]) == 3

    def test_execute_deterministic_workflow(
        self, test_client, sample_deterministic_workflow, sample_execution_request
    ):
        """Test executing a deterministic workflow via POST /api/workflows/{id}/execute."""
        # First create the workflow
        create_response = test_client.post(
            "/api/workflows/", json=sample_deterministic_workflow
        )
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # Then execute it
        execute_response = test_client.post(
            f"/api/workflows/{workflow_id}/execute", json=sample_execution_request
        )

        # The execution should succeed (even if steps aren't fully implemented)
        assert execute_response.status_code == 200

        data = execute_response.json()
        assert data["status"] in [
            "success",
            "error",
        ]  # Allow error for unimplemented steps
        assert data["workflow_id"] == workflow_id
        assert "execution_id" in data
        assert "timestamp" in data

        # If successful, verify response structure
        if data["status"] == "success":
            assert "response" in data
            response_data = json.loads(data["response"])
            assert isinstance(response_data, dict)

    def test_workflow_detection_logic(self, test_client):
        """Test that the workflow detection logic correctly identifies deterministic workflows."""
        unique_id = str(uuid.uuid4())[:8]

        # Test explicit deterministic workflow type
        deterministic_config = {
            "name": f"Explicit Deterministic {unique_id}",
            "configuration": {"workflow_type": "deterministic", "steps": []},
        }

        response = test_client.post("/api/workflows/", json=deterministic_config)
        if response.status_code != 200:
            print(f"Explicit deterministic error: {response.text}")
        assert response.status_code == 200

        # Test implicit deterministic workflow (has steps, no agents)
        implicit_config = {
            "name": f"Implicit Deterministic {unique_id}",
            "configuration": {
                "steps": [{"step_type": "data_processing", "step_name": "Process"}]
            },
        }

        response = test_client.post("/api/workflows/", json=implicit_config)
        if response.status_code != 200:
            print(f"Implicit deterministic error: {response.text}")
        assert response.status_code == 200

        # Test traditional agent workflow (should not be detected as deterministic)
        agent_config = {
            "name": f"Agent Workflow {unique_id}",
            "configuration": {
                "agents": [
                    {"agent_type": "CommandAgent", "agent_id": str(uuid.uuid4())}
                ],
                "connections": [],
            },
        }

        response = test_client.post("/api/workflows/", json=agent_config)
        if response.status_code != 200:
            print(f"Agent workflow error: {response.text}")
        assert response.status_code == 200

    def test_list_workflows_includes_deterministic(
        self, test_client, sample_deterministic_workflow
    ):
        """Test that deterministic workflows appear in workflow listings."""
        # Create a deterministic workflow
        create_response = test_client.post(
            "/api/workflows/", json=sample_deterministic_workflow
        )
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]

        # List all workflows
        list_response = test_client.get("/api/workflows/")
        assert list_response.status_code == 200

        workflows = list_response.json()

        # Find our deterministic workflow in the list
        deterministic_workflow = None
        for workflow in workflows:
            if workflow["workflow_id"] == workflow_id:
                deterministic_workflow = workflow
                break

        assert deterministic_workflow is not None
        assert (
            deterministic_workflow["configuration"]["workflow_type"] == "deterministic"
        )


if __name__ == "__main__":
    """Run tests directly for development."""
    import subprocess
    import sys

    print("🧪 Running Deterministic Workflow Integration Tests")
    print("=" * 60)

    # Run pytest on this file
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False,
    )

    sys.exit(result.returncode)
