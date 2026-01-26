"""
Integration tests for Policy Management API - Simplified Version

These tests use FastAPI's dependency override system to mock authentication.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import policies
from app.services.policy_service import PolicyService, get_policy_service
from app.core.deps import get_current_superuser
from app.db.models import User


@pytest.fixture
def mock_superuser():
    """Mock superuser for authentication"""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "admin@example.com"
    user.is_superuser = True
    return user


@pytest.fixture
def mock_policy_service():
    """Mock PolicyService"""
    service = MagicMock(spec=PolicyService)
    return service


@pytest.fixture
def app(mock_superuser, mock_policy_service):
    """Create a test FastAPI app with dependency overrides"""
    test_app = FastAPI()
    test_app.include_router(policies.router, prefix="/api", tags=["policies"])

    # Override dependencies
    test_app.dependency_overrides[get_current_superuser] = lambda: mock_superuser
    test_app.dependency_overrides[get_policy_service] = lambda: mock_policy_service

    return test_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


class TestPolicyGenerateEndpoint:
    """Test POST /api/policies/generate endpoint"""

    def test_generate_policy_success(self, client, mock_policy_service):
        """Test successful policy generation"""
        # Mock service methods
        mock_policy_service.generate_service_policy = AsyncMock(
            return_value="package rbac\n\nallow = true"
        )
        mock_policy_service.validate_rego_syntax = AsyncMock(return_value=(True, None))
        mock_policy_service.upload_policy = AsyncMock(return_value=True)

        response = client.post(
            "/api/policies/generate",
            json={
                "service_name": "workflow_engine",
                "resource_type": "workflow",
                "actions": {
                    "admin": ["create_workflow", "edit_workflow", "view_workflow"],
                    "viewer": ["view_workflow"],
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "workflow_engine" in data["message"]
        assert data["module_name"] == "rbac/workflow_engine"
        assert "rego_code" in data

    def test_generate_policy_invalid_syntax(self, client, mock_policy_service):
        """Test policy generation with invalid syntax"""
        mock_policy_service.generate_service_policy = AsyncMock(
            return_value="invalid rego"
        )
        mock_policy_service.validate_rego_syntax = AsyncMock(
            return_value=(False, "syntax error")
        )

        response = client.post(
            "/api/policies/generate",
            json={
                "service_name": "test_service",
                "resource_type": "test",
                "actions": {"admin": ["test_action"]},
            },
        )

        assert response.status_code == 400
        assert "syntax error" in response.json()["detail"]


class TestPolicyUploadEndpoint:
    """Test POST /api/policies/upload endpoint"""

    def test_upload_custom_policy_success(self, client, mock_policy_service):
        """Test successful custom policy upload"""
        mock_policy_service.validate_rego_syntax = AsyncMock(return_value=(True, None))
        mock_policy_service.upload_policy = AsyncMock(return_value=True)

        response = client.post(
            "/api/policies/upload",
            json={
                "module_name": "rbac/custom",
                "rego_code": "package rbac\n\nimport rego.v1\n\nallow = true",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "rbac/custom" in data["message"]


class TestPolicyListEndpoint:
    """Test GET /api/policies endpoint"""

    def test_list_policies_success(self, client, mock_policy_service):
        """Test successful policy listing"""
        mock_policy_service.list_policies = AsyncMock(
            return_value=[
                {"id": "rbac/core", "name": "rbac/core"},
                {"id": "rbac/workflows", "name": "rbac/workflows"},
            ]
        )

        response = client.get("/api/policies")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert {"id": "rbac/core", "name": "rbac/core"} in data


class TestPolicyGetEndpoint:
    """Test GET /api/policies/{module_name} endpoint"""

    def test_get_policy_success(self, client, mock_policy_service):
        """Test successful policy retrieval"""
        mock_policy_service.get_policy = AsyncMock(
            return_value="package rbac\n\nallow = true"
        )

        response = client.get("/api/policies/rbac/workflows")

        assert response.status_code == 200
        data = response.json()
        assert data["module_name"] == "rbac/workflows"
        assert "package rbac" in data["rego_code"]

    def test_get_policy_not_found(self, client, mock_policy_service):
        """Test getting non-existent policy"""
        mock_policy_service.get_policy = AsyncMock(return_value=None)

        response = client.get("/api/policies/rbac/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestPolicyDeleteEndpoint:
    """Test DELETE /api/policies/{module_name} endpoint"""

    def test_delete_policy_success(self, client, mock_policy_service):
        """Test successful policy deletion"""
        mock_policy_service.delete_policy = AsyncMock(return_value=True)

        response = client.delete("/api/policies/rbac/test")

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_delete_policy_failure(self, client, mock_policy_service):
        """Test failed policy deletion"""
        mock_policy_service.delete_policy = AsyncMock(return_value=False)

        response = client.delete("/api/policies/rbac/test")

        assert response.status_code == 500
        assert "Failed to delete policy" in response.json()["detail"]
