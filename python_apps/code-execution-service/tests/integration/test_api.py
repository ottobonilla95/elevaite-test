"""Integration tests for the API endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client: TestClient):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client: TestClient):
        """Test that health endpoint returns status field."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_returns_nsjail_available(self, client: TestClient):
        """Test that health endpoint returns nsjail_available field."""
        response = client.get("/health")
        data = response.json()

        assert "nsjail_available" in data
        assert isinstance(data["nsjail_available"], bool)


class TestRootEndpoint:
    """Tests for the / root endpoint."""

    def test_root_returns_200(self, client: TestClient):
        """Test that root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_service_info(self, client: TestClient):
        """Test that root endpoint returns service info."""
        response = client.get("/")
        data = response.json()

        assert "service" in data
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"


class TestExecuteEndpoint:
    """Tests for the /execute endpoint."""

    def test_execute_returns_200_for_valid_code(self, client: TestClient):
        """Test that execute endpoint returns 200 for valid code."""
        response = client.post(
            "/execute",
            json={"code": "print('hello')"},
        )
        assert response.status_code == 200

    def test_execute_returns_validation_errors_for_blocked_code(self, client: TestClient):
        """Test that execute returns validation errors for blocked code."""
        response = client.post(
            "/execute",
            json={"code": "import os"},
        )
        data = response.json()

        assert response.status_code == 200  # API returns 200 with error in body
        assert data["success"] is False
        assert data["validation_errors"] is not None
        assert len(data["validation_errors"]) > 0

    def test_execute_rejects_unsupported_language(self, client: TestClient):
        """Test that execute rejects unsupported languages."""
        response = client.post(
            "/execute",
            json={
                "language": "ruby",
                "code": "puts 'hello'",
            },
        )
        data = response.json()

        assert data["success"] is False
        assert data["error"] is not None
        assert "Unsupported language" in data["error"]

    def test_execute_accepts_python_language(self, client: TestClient):
        """Test that execute accepts Python language explicitly."""
        response = client.post(
            "/execute",
            json={
                "language": "python",
                "code": "print('hello')",
            },
        )
        data = response.json()

        # Should not fail due to language
        assert data.get("error") is None or "Unsupported language" not in data["error"]

    def test_execute_with_input_data(self, client: TestClient):
        """Test that execute accepts input_data parameter."""
        response = client.post(
            "/execute",
            json={
                "code": "print(input_data)",
                "input_data": {"key": "value"},
            },
        )
        assert response.status_code == 200

    def test_execute_with_custom_timeout(self, client: TestClient):
        """Test that execute accepts custom timeout."""
        response = client.post(
            "/execute",
            json={
                "code": "print('hello')",
                "timeout_seconds": 10,
            },
        )
        assert response.status_code == 200

    def test_execute_with_custom_memory(self, client: TestClient):
        """Test that execute accepts custom memory limit."""
        response = client.post(
            "/execute",
            json={
                "code": "print('hello')",
                "memory_mb": 128,
            },
        )
        assert response.status_code == 200

    def test_execute_validates_timeout_range(self, client: TestClient):
        """Test that execute validates timeout is within range."""
        response = client.post(
            "/execute",
            json={
                "code": "print('hello')",
                "timeout_seconds": 0,  # Below minimum
            },
        )
        # Pydantic should reject this with 422
        assert response.status_code == 422

    def test_execute_validates_memory_range(self, client: TestClient):
        """Test that execute validates memory is within range."""
        response = client.post(
            "/execute",
            json={
                "code": "print('hello')",
                "memory_mb": 10,  # Below minimum of 64
            },
        )
        # Pydantic should reject this with 422
        assert response.status_code == 422

    def test_execute_requires_code(self, client: TestClient):
        """Test that execute requires code field."""
        response = client.post(
            "/execute",
            json={},
        )
        # Pydantic should reject this with 422
        assert response.status_code == 422

    def test_execute_rejects_empty_code(self, client: TestClient):
        """Test that execute rejects empty code string."""
        response = client.post(
            "/execute",
            json={"code": ""},
        )
        # Pydantic min_length=1 should reject this
        assert response.status_code == 422

    def test_execute_response_structure(self, client: TestClient):
        """Test that execute response has expected structure."""
        response = client.post(
            "/execute",
            json={"code": "print('hello')"},
        )
        data = response.json()

        # Check all expected fields are present
        assert "success" in data
        assert "stdout" in data
        assert "stderr" in data
        assert "exit_code" in data
        assert "execution_time_ms" in data

