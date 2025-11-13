"""
Tests for Steps Router

Tests all step registration and management endpoints:
- POST /steps/register - Register custom step functions
- GET /steps - List all registered steps
- GET /steps/{step_type} - Get specific step information
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def sample_step_config():
    """Sample step configuration for testing"""
    return {
        "step_type": "custom_processor",
        "name": "Custom Data Processor",
        "function_reference": "http://example.com/process",
        "execution_type": "rpc",
        "description": "A custom data processing step",
        "parameters": {
            "input_data": {"type": "string", "required": True},
            "options": {"type": "object", "required": False},
        },
    }


@pytest.fixture
def registered_steps_list():
    """Sample list of registered steps"""
    return [
        {
            "step_id": "step-001",
            "step_type": "trigger",
            "name": "Trigger Step",
            "execution_type": "local",
            "description": "Workflow trigger step",
        },
        {
            "step_id": "step-002",
            "step_type": "data_input",
            "name": "Data Input Step",
            "execution_type": "local",
            "description": "Input data step",
        },
        {
            "step_id": "step-003",
            "step_type": "custom_processor",
            "name": "Custom Processor",
            "execution_type": "rpc",
            "description": "Custom processing step",
        },
    ]


@pytest.mark.api
class TestRegisterStep:
    """Tests for POST /steps/register endpoint"""

    @pytest.mark.api
    def test_register_step_success(self, authenticated_client: TestClient, sample_step_config):
        """Test successfully registering a new step"""
        with patch.object(
            authenticated_client.app.state.step_registry, "register_step", new_callable=AsyncMock
        ) as mock_register:
            mock_register.return_value = "step-123"

            response = authenticated_client.post("/steps/register", json=sample_step_config)

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Step registered successfully"
            assert data["step_type"] == "custom_processor"
            mock_register.assert_called_once_with(sample_step_config)

    @pytest.mark.api
    def test_register_step_missing_required_field(self, authenticated_client: TestClient):
        """Test registering step with missing required field"""
        incomplete_config = {
            "step_type": "custom_step",
            "name": "Custom Step",
            # Missing function_reference and execution_type
        }

        with patch.object(
            authenticated_client.app.state.step_registry, "register_step", new_callable=AsyncMock
        ) as mock_register:
            mock_register.side_effect = ValueError("Missing required field: function_reference")

            response = authenticated_client.post("/steps/register", json=incomplete_config)

            assert response.status_code == 500
            assert "Missing required field" in response.json()["detail"]

    @pytest.mark.api
    def test_register_step_duplicate_type(self, authenticated_client: TestClient, sample_step_config):
        """Test registering step with duplicate step_type"""
        with patch.object(
            authenticated_client.app.state.step_registry, "register_step", new_callable=AsyncMock
        ) as mock_register:
            mock_register.side_effect = ValueError("Step type already registered")

            response = authenticated_client.post("/steps/register", json=sample_step_config)

            assert response.status_code == 500
            assert "already registered" in response.json()["detail"]

    @pytest.mark.api
    def test_register_step_invalid_execution_type(self, authenticated_client: TestClient):
        """Test registering step with invalid execution_type"""
        invalid_config = {
            "step_type": "custom_step",
            "name": "Custom Step",
            "function_reference": "http://example.com/step",
            "execution_type": "invalid_type",
        }

        with patch.object(
            authenticated_client.app.state.step_registry, "register_step", new_callable=AsyncMock
        ) as mock_register:
            mock_register.side_effect = ValueError("Invalid execution_type")

            response = authenticated_client.post("/steps/register", json=invalid_config)

            assert response.status_code == 500

    @pytest.mark.api
    def test_register_step_with_rpc_endpoint(self, authenticated_client: TestClient):
        """Test registering RPC step with endpoint"""
        rpc_config = {
            "step_type": "rpc_processor",
            "name": "RPC Processor",
            "function_reference": "http://rpc-server:8080/process",
            "execution_type": "rpc",
            "timeout": 30,
        }

        with patch.object(
            authenticated_client.app.state.step_registry, "register_step", new_callable=AsyncMock
        ) as mock_register:
            mock_register.return_value = "step-rpc-001"

            response = authenticated_client.post("/steps/register", json=rpc_config)

            assert response.status_code == 200
            assert response.json()["step_type"] == "rpc_processor"

    @pytest.mark.api
    def test_register_step_with_rest_api(self, authenticated_client: TestClient):
        """Test registering REST API step"""
        rest_config = {
            "step_type": "rest_api_call",
            "name": "REST API Call",
            "function_reference": "https://api.example.com/v1/process",
            "execution_type": "rest",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
        }

        with patch.object(
            authenticated_client.app.state.step_registry, "register_step", new_callable=AsyncMock
        ) as mock_register:
            mock_register.return_value = "step-rest-001"

            response = authenticated_client.post("/steps/register", json=rest_config)

            assert response.status_code == 200
            assert response.json()["step_type"] == "rest_api_call"


@pytest.mark.api
class TestListRegisteredSteps:
    """Tests for GET /steps endpoint"""

    @pytest.mark.api
    def test_list_steps_success(self, authenticated_client: TestClient, registered_steps_list):
        """Test listing all registered steps"""
        with patch.object(
            authenticated_client.app.state.step_registry, "get_registered_steps", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = registered_steps_list

            response = authenticated_client.get("/steps/")

            assert response.status_code == 200
            data = response.json()
            assert "steps" in data
            assert "total" in data
            assert data["total"] == 3
            assert len(data["steps"]) == 3
            assert data["steps"][0]["step_type"] == "trigger"
            mock_list.assert_called_once()

    @pytest.mark.api
    def test_list_steps_empty(self, authenticated_client: TestClient):
        """Test listing when no steps are registered"""
        with patch.object(
            authenticated_client.app.state.step_registry, "get_registered_steps", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = []

            response = authenticated_client.get("/steps/")

            assert response.status_code == 200
            data = response.json()
            assert data["steps"] == []
            assert data["total"] == 0

    @pytest.mark.api
    def test_list_steps_error_handling(self, authenticated_client: TestClient):
        """Test error handling when listing steps fails"""
        with patch.object(
            authenticated_client.app.state.step_registry, "get_registered_steps", new_callable=AsyncMock
        ) as mock_list:
            mock_list.side_effect = Exception("Database connection failed")

            response = authenticated_client.get("/steps/")

            assert response.status_code == 500
            assert "Database connection failed" in response.json()["detail"]

    @pytest.mark.api
    def test_list_steps_includes_all_types(self, authenticated_client: TestClient):
        """Test that list includes local, RPC, and REST steps"""
        mixed_steps = [
            {"step_type": "local_step", "execution_type": "local"},
            {"step_type": "rpc_step", "execution_type": "rpc"},
            {"step_type": "rest_step", "execution_type": "rest"},
        ]

        with patch.object(
            authenticated_client.app.state.step_registry, "get_registered_steps", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = mixed_steps

            response = authenticated_client.get("/steps/")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            execution_types = [step["execution_type"] for step in data["steps"]]
            assert "local" in execution_types
            assert "rpc" in execution_types
            assert "rest" in execution_types


@pytest.mark.api
class TestGetStepInfo:
    """Tests for GET /steps/{step_type} endpoint"""

    @pytest.mark.api
    def test_get_step_info_success(self, authenticated_client: TestClient):
        """Test getting information about a specific step"""
        step_info = {
            "step_id": "step-001",
            "step_type": "custom_processor",
            "name": "Custom Processor",
            "execution_type": "rpc",
            "function_reference": "http://example.com/process",
            "description": "Custom data processor",
            "parameters": {
                "input": {"type": "string", "required": True},
            },
        }

        with patch.object(
            authenticated_client.app.state.step_registry, "get_step_info", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = step_info

            response = authenticated_client.get("/steps/custom_processor")

            assert response.status_code == 200
            data = response.json()
            assert data["step_type"] == "custom_processor"
            assert data["execution_type"] == "rpc"
            assert "parameters" in data
            mock_get.assert_called_once_with("custom_processor")

    @pytest.mark.api
    def test_get_step_info_not_found(self, authenticated_client: TestClient):
        """Test getting info for non-existent step type"""
        with patch.object(
            authenticated_client.app.state.step_registry, "get_step_info", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            response = authenticated_client.get("/steps/nonexistent_step")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.api
    def test_get_step_info_builtin_step(self, authenticated_client: TestClient):
        """Test getting info for built-in step type"""
        builtin_step = {
            "step_id": "builtin-trigger",
            "step_type": "trigger",
            "name": "Trigger Step",
            "execution_type": "local",
            "description": "Workflow trigger step",
        }

        with patch.object(
            authenticated_client.app.state.step_registry, "get_step_info", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = builtin_step

            response = authenticated_client.get("/steps/trigger")

            assert response.status_code == 200
            data = response.json()
            assert data["step_type"] == "trigger"
            assert data["execution_type"] == "local"

    @pytest.mark.api
    def test_get_step_info_error_handling(self, authenticated_client: TestClient):
        """Test error handling when getting step info fails"""
        with patch.object(
            authenticated_client.app.state.step_registry, "get_step_info", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = Exception("Internal error")

            response = authenticated_client.get("/steps/some_step")

            assert response.status_code == 500
            assert "Internal error" in response.json()["detail"]

    @pytest.mark.api
    def test_get_step_info_with_special_characters(self, authenticated_client: TestClient):
        """Test getting step info with special characters in step_type"""
        step_info = {
            "step_type": "custom-processor_v2",
            "name": "Custom Processor V2",
        }

        with patch.object(
            authenticated_client.app.state.step_registry, "get_step_info", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = step_info

            response = authenticated_client.get("/steps/custom-processor_v2")

            assert response.status_code == 200
            assert response.json()["step_type"] == "custom-processor_v2"

