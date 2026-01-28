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
    """Sample step configuration for testing using current StepConfigCreate schema"""
    return {
        "step_type": "custom_processor",
        "name": "Custom Data Processor",
        "description": "A custom data processing step",
        "category": "data_processing",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "input_data": {"type": "string"},
                "options": {"type": "object"},
            },
            "required": ["input_data"],
        },
        "handler_url": "http://example.com/process",
        "handler_method": "POST",
    }


@pytest.fixture
def registered_steps_list():
    """Sample list of registered steps matching StepInfoResponse schema"""
    return [
        {
            "step_type": "trigger",
            "name": "Trigger Step",
            "description": "Workflow trigger step",
            "parameters_schema": {},
            "version": "1.0.0",
            "is_async": True,
        },
        {
            "step_type": "data_input",
            "name": "Data Input Step",
            "description": "Input data step",
            "parameters_schema": {},
            "version": "1.0.0",
            "is_async": True,
        },
        {
            "step_type": "custom_processor",
            "name": "Custom Processor",
            "description": "Custom processing step",
            "parameters_schema": {},
            "version": "1.0.0",
            "is_async": True,
        },
    ]


@pytest.mark.api
class TestRegisterStep:
    """Tests for POST /steps/register endpoint"""

    @pytest.mark.api
    def test_register_step_success(
        self, authenticated_client: TestClient, sample_step_config
    ):
        """Test successfully registering a new step"""
        with patch.object(
            authenticated_client.app.state.step_registry,
            "register_step",
            new_callable=AsyncMock,
        ) as mock_register:
            mock_register.return_value = "step-123"

            response = authenticated_client.post(
                "/steps/register", json=sample_step_config
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Step registered successfully"
            assert data["step_type"] == "custom_processor"
            # Verify register_step was called (schema transforms the input)
            mock_register.assert_called_once()

    @pytest.mark.api
    def test_register_step_missing_required_field(
        self, authenticated_client: TestClient
    ):
        """Test registering step with missing required field - name is required"""
        incomplete_config = {
            "step_type": "custom_step",
            # Missing name field
        }

        # FastAPI will return 422 for validation errors
        response = authenticated_client.post("/steps/register", json=incomplete_config)
        assert response.status_code == 422

    @pytest.mark.api
    def test_register_step_duplicate_type(
        self, authenticated_client: TestClient, sample_step_config
    ):
        """Test registering step with duplicate step_type"""
        with patch.object(
            authenticated_client.app.state.step_registry,
            "register_step",
            new_callable=AsyncMock,
        ) as mock_register:
            mock_register.side_effect = ValueError("Step type already registered")

            response = authenticated_client.post(
                "/steps/register", json=sample_step_config
            )

            assert response.status_code == 500
            assert "already registered" in response.json()["detail"]

    @pytest.mark.api
    def test_register_step_with_handler_url(self, authenticated_client: TestClient):
        """Test registering step with remote handler URL"""
        config = {
            "step_type": "remote_processor",
            "name": "Remote Processor",
            "description": "Processes data via remote endpoint",
            "handler_url": "http://processor-service:8080/process",
            "handler_method": "POST",
        }

        with patch.object(
            authenticated_client.app.state.step_registry,
            "register_step",
            new_callable=AsyncMock,
        ) as mock_register:
            mock_register.return_value = "step-remote-001"

            response = authenticated_client.post("/steps/register", json=config)

            assert response.status_code == 200
            assert response.json()["step_type"] == "remote_processor"

    @pytest.mark.api
    def test_register_step_with_parameters_schema(
        self, authenticated_client: TestClient
    ):
        """Test registering step with JSON schema for parameters"""
        config = {
            "step_type": "schema_step",
            "name": "Schema Step",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "count": {"type": "integer", "minimum": 1},
                },
                "required": ["input"],
            },
        }

        with patch.object(
            authenticated_client.app.state.step_registry,
            "register_step",
            new_callable=AsyncMock,
        ) as mock_register:
            mock_register.return_value = "step-schema-001"

            response = authenticated_client.post("/steps/register", json=config)

            assert response.status_code == 200
            assert response.json()["step_type"] == "schema_step"


@pytest.mark.api
class TestListRegisteredSteps:
    """Tests for GET /steps endpoint"""

    @pytest.mark.api
    def test_list_steps_success(
        self, authenticated_client: TestClient, registered_steps_list
    ):
        """Test listing all registered steps"""
        with patch.object(
            authenticated_client.app.state.step_registry,
            "get_registered_steps",
            new_callable=AsyncMock,
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
            authenticated_client.app.state.step_registry,
            "get_registered_steps",
            new_callable=AsyncMock,
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
            authenticated_client.app.state.step_registry,
            "get_registered_steps",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.side_effect = Exception("Database connection failed")

            response = authenticated_client.get("/steps/")

            assert response.status_code == 500
            assert "Database connection failed" in response.json()["detail"]

    @pytest.mark.api
    def test_list_steps_with_mixed_categories(self, authenticated_client: TestClient):
        """Test that list includes steps from different categories"""
        mixed_steps = [
            {
                "step_type": "trigger",
                "name": "Trigger",
                "description": "Workflow trigger",
                "parameters_schema": {},
                "version": "1.0.0",
                "is_async": True,
            },
            {
                "step_type": "data_input",
                "name": "Data Input",
                "description": "Input data",
                "parameters_schema": {},
                "version": "1.0.0",
                "is_async": True,
            },
        ]

        with patch.object(
            authenticated_client.app.state.step_registry,
            "get_registered_steps",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = mixed_steps

            response = authenticated_client.get("/steps/")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            step_types = [step["step_type"] for step in data["steps"]]
            assert "trigger" in step_types
            assert "data_input" in step_types


@pytest.mark.api
class TestGetStepInfo:
    """Tests for GET /steps/{step_type} endpoint"""

    @pytest.mark.api
    def test_get_step_info_success(self, authenticated_client: TestClient):
        """Test getting information about a specific step"""
        step_info = {
            "step_type": "custom_processor",
            "name": "Custom Processor",
            "description": "Custom data processor",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                },
                "required": ["input"],
            },
            "version": "1.0.0",
            "is_async": True,
            "handler_url": "http://example.com/process",
        }

        with patch.object(
            authenticated_client.app.state.step_registry,
            "get_step_info",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = step_info

            response = authenticated_client.get("/steps/custom_processor")

            assert response.status_code == 200
            data = response.json()
            assert data["step_type"] == "custom_processor"
            assert data["name"] == "Custom Processor"
            assert "parameters_schema" in data
            mock_get.assert_called_once_with("custom_processor")

    @pytest.mark.api
    def test_get_step_info_not_found(self, authenticated_client: TestClient):
        """Test getting info for non-existent step type"""
        with patch.object(
            authenticated_client.app.state.step_registry,
            "get_step_info",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = None

            response = authenticated_client.get("/steps/nonexistent_step")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.api
    def test_get_step_info_builtin_step(self, authenticated_client: TestClient):
        """Test getting info for built-in step type"""
        builtin_step = {
            "step_type": "trigger",
            "name": "Trigger Step",
            "description": "Workflow trigger step",
            "parameters_schema": {},
            "version": "1.0.0",
            "is_async": True,
        }

        with patch.object(
            authenticated_client.app.state.step_registry,
            "get_step_info",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = builtin_step

            response = authenticated_client.get("/steps/trigger")

            assert response.status_code == 200
            data = response.json()
            assert data["step_type"] == "trigger"
            assert data["name"] == "Trigger Step"

    @pytest.mark.api
    def test_get_step_info_error_handling(self, authenticated_client: TestClient):
        """Test error handling when getting step info fails"""
        with patch.object(
            authenticated_client.app.state.step_registry,
            "get_step_info",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.side_effect = Exception("Internal error")

            response = authenticated_client.get("/steps/some_step")

            assert response.status_code == 500
            assert "Internal error" in response.json()["detail"]

    @pytest.mark.api
    def test_get_step_info_with_special_characters(
        self, authenticated_client: TestClient
    ):
        """Test getting step info with special characters in step_type"""
        step_info = {
            "step_type": "custom-processor_v2",
            "name": "Custom Processor V2",
            "parameters_schema": {},
            "version": "2.0.0",
            "is_async": False,
        }

        with patch.object(
            authenticated_client.app.state.step_registry,
            "get_step_info",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = step_info

            response = authenticated_client.get("/steps/custom-processor_v2")

            assert response.status_code == 200
            assert response.json()["step_type"] == "custom-processor_v2"


@pytest.mark.api
class TestListBuiltinVariables:
    """Tests for GET /steps/variables/builtin endpoint"""

    @pytest.mark.api
    def test_list_builtin_variables_success(self, authenticated_client: TestClient):
        """Test listing all builtin variables returns expected structure"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "variables" in data
        assert "total" in data
        assert isinstance(data["variables"], list)
        assert data["total"] == len(data["variables"])
        assert data["total"] > 0

    @pytest.mark.api
    def test_builtin_variables_have_required_fields(
        self, authenticated_client: TestClient
    ):
        """Test that each variable has all required fields"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        for var in data["variables"]:
            assert "name" in var, "Variable missing 'name' field"
            assert "description" in var, (
                f"Variable {var.get('name')} missing 'description'"
            )
            assert "category" in var, f"Variable {var.get('name')} missing 'category'"
            assert "source" in var, f"Variable {var.get('name')} missing 'source'"
            # example is optional but should be present for most
            assert "example" in var, f"Variable {var.get('name')} missing 'example'"

    @pytest.mark.api
    def test_builtin_variables_include_time_variables(
        self, authenticated_client: TestClient
    ):
        """Test that time-related variables are included"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        var_names = [v["name"] for v in data["variables"]]

        # Check core time variables
        assert "current_time" in var_names
        assert "current_date" in var_names
        assert "current_timestamp" in var_names
        assert "current_year" in var_names
        assert "current_month" in var_names
        assert "current_day" in var_names

        # Check UTC/local variants
        assert "current_time_utc" in var_names
        assert "current_date_utc" in var_names
        assert "current_time_local" in var_names
        assert "current_date_local" in var_names

    @pytest.mark.api
    def test_builtin_variables_include_context_variables(
        self, authenticated_client: TestClient
    ):
        """Test that context variables are included"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        var_names = [v["name"] for v in data["variables"]]

        # Check context variables
        assert "execution_id" in var_names
        assert "workflow_id" in var_names
        assert "user_id" in var_names
        assert "user_name" in var_names
        assert "session_id" in var_names

    @pytest.mark.api
    def test_builtin_variables_include_identifiers(
        self, authenticated_client: TestClient
    ):
        """Test that identifier variables are included"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        var_names = [v["name"] for v in data["variables"]]

        assert "uuid" in var_names

    @pytest.mark.api
    def test_builtin_variables_valid_categories(self, authenticated_client: TestClient):
        """Test that all variables have valid categories"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        valid_categories = {"time", "context", "identifier", "other"}

        for var in data["variables"]:
            assert var["category"] in valid_categories, (
                f"Variable {var['name']} has invalid category: {var['category']}"
            )

    @pytest.mark.api
    def test_builtin_variables_valid_sources(self, authenticated_client: TestClient):
        """Test that all variables have valid source types"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        valid_sources = {"builtin", "context"}

        for var in data["variables"]:
            assert var["source"] in valid_sources, (
                f"Variable {var['name']} has invalid source: {var['source']}"
            )

    @pytest.mark.api
    def test_builtin_variables_sorted_by_category(
        self, authenticated_client: TestClient
    ):
        """Test that variables are sorted by category then name"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        # Extract category-name tuples
        category_names = [(v["category"], v["name"]) for v in data["variables"]]

        # Check that list is sorted
        assert category_names == sorted(category_names), (
            "Variables should be sorted by category then name"
        )

    @pytest.mark.api
    def test_builtin_variables_context_source_correct(
        self, authenticated_client: TestClient
    ):
        """Test that context variables have source='context'"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        context_vars = [
            "workflow_id",
            "user_id",
            "user_name",
            "session_id",
            "execution_id",
        ]

        for var in data["variables"]:
            if var["name"] in context_vars:
                assert var["source"] == "context", (
                    f"Variable {var['name']} should have source='context'"
                )

    @pytest.mark.api
    def test_builtin_variables_time_source_correct(
        self, authenticated_client: TestClient
    ):
        """Test that time variables have source='builtin'"""
        response = authenticated_client.get("/steps/variables/builtin")

        assert response.status_code == 200
        data = response.json()

        time_vars = [
            "current_time",
            "current_time_utc",
            "current_time_local",
            "current_date",
            "current_date_utc",
            "current_date_local",
            "current_timestamp",
            "current_year",
            "current_month",
            "current_day",
            "current_hour",
            "current_minute",
        ]

        for var in data["variables"]:
            if var["name"] in time_vars:
                assert var["source"] == "builtin", (
                    f"Variable {var['name']} should have source='builtin'"
                )
