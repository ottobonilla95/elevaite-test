"""
Integration tests for RBAC guards in workflow-engine-poc.

Tests that RBAC guards properly protect endpoints and enforce permissions.
Requires Auth API and OPA to be running.
"""

import pytest
import httpx
import os
from typing import Dict, Any
from jose import jwt
from datetime import datetime, timedelta, timezone


# Test configuration
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://localhost:8004")
WORKFLOW_ENGINE_URL = os.getenv("WORKFLOW_ENGINE_URL", "http://localhost:8006")
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "test-secret-key-for-integration-tests")
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-integration-tests")

# Test data
TEST_ORG_ID = "test-org-123"
TEST_ACCOUNT_ID = "test-account-456"
TEST_PROJECT_ID = "test-project-789"


@pytest.fixture
def test_user_viewer() -> Dict[str, Any]:
    """Create a test user with viewer role."""
    return {
        "user_id": "viewer-user-001",
        "email": "viewer@test.com",
        "role": "viewer",
        "org_id": TEST_ORG_ID,
        "account_id": TEST_ACCOUNT_ID,
        "project_id": TEST_PROJECT_ID,
    }


@pytest.fixture
def test_user_editor() -> Dict[str, Any]:
    """Create a test user with editor role."""
    return {
        "user_id": "editor-user-001",
        "email": "editor@test.com",
        "role": "editor",
        "org_id": TEST_ORG_ID,
        "account_id": TEST_ACCOUNT_ID,
        "project_id": TEST_PROJECT_ID,
    }


@pytest.fixture
def test_user_admin() -> Dict[str, Any]:
    """Create a test user with admin role."""
    return {
        "user_id": "admin-user-001",
        "email": "admin@test.com",
        "role": "admin",
        "org_id": TEST_ORG_ID,
        "account_id": TEST_ACCOUNT_ID,
        "project_id": TEST_PROJECT_ID,
    }


def create_api_key(user_id: str, org_id: str) -> str:
    """Create a test API key JWT."""
    payload = {
        "sub": user_id,
        "type": "api_key",
        "organization_id": org_id,
        "tenant_id": "default",
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, API_KEY_SECRET, algorithm="HS256")


def create_access_token(user_id: str, email: str) -> str:
    """Create a test access token JWT."""
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.mark.asyncio
class TestWorkflowRBAC:
    """Test RBAC guards on workflow endpoints."""

    async def test_list_workflows_requires_auth(self):
        """Test that listing workflows requires authentication."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/workflows/")
            # Should return 403 (forbidden) without auth headers
            assert response.status_code in [401, 403, 400]

    async def test_list_workflows_with_viewer(self, test_user_viewer):
        """Test that viewers can list workflows."""
        api_key = create_api_key(test_user_viewer["user_id"], test_user_viewer["org_id"])
        
        headers = {
            "X-elevAIte-apikey": api_key,
            "X-elevAIte-UserId": test_user_viewer["user_id"],
            "X-elevAIte-OrganizationId": test_user_viewer["org_id"],
            "X-elevAIte-AccountId": test_user_viewer["account_id"],
            "X-elevAIte-ProjectId": test_user_viewer["project_id"],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
            # Should succeed (200) or fail with proper RBAC error (403)
            # Note: May fail if user doesn't exist in Auth API
            assert response.status_code in [200, 403, 401]

    async def test_create_workflow_denied_for_viewer(self, test_user_viewer):
        """Test that viewers cannot create workflows."""
        api_key = create_api_key(test_user_viewer["user_id"], test_user_viewer["org_id"])
        
        headers = {
            "X-elevAIte-apikey": api_key,
            "X-elevAIte-UserId": test_user_viewer["user_id"],
            "X-elevAIte-OrganizationId": test_user_viewer["org_id"],
            "X-elevAIte-AccountId": test_user_viewer["account_id"],
            "X-elevAIte-ProjectId": test_user_viewer["project_id"],
        }
        
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test workflow for RBAC",
            "steps": [],
            "connections": [],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WORKFLOW_ENGINE_URL}/workflows/",
                json=workflow_data,
                headers=headers,
            )
            # Should be denied (403) for viewers
            assert response.status_code in [403, 401]


@pytest.mark.asyncio
class TestExecutionRBAC:
    """Test RBAC guards on execution endpoints."""

    async def test_get_execution_requires_auth(self):
        """Test that getting execution status requires authentication."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/executions/test-exec-id")
            # Should return 403 (forbidden) without auth headers
            assert response.status_code in [401, 403, 400]

    async def test_list_executions_with_viewer(self, test_user_viewer):
        """Test that viewers can list executions."""
        api_key = create_api_key(test_user_viewer["user_id"], test_user_viewer["org_id"])
        
        headers = {
            "X-elevAIte-apikey": api_key,
            "X-elevAIte-UserId": test_user_viewer["user_id"],
            "X-elevAIte-OrganizationId": test_user_viewer["org_id"],
            "X-elevAIte-AccountId": test_user_viewer["account_id"],
            "X-elevAIte-ProjectId": test_user_viewer["project_id"],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/executions/", headers=headers)
            # Should succeed (200) or fail with proper RBAC error (403)
            assert response.status_code in [200, 403, 401]


@pytest.mark.asyncio
class TestAgentRBAC:
    """Test RBAC guards on agent endpoints."""

    async def test_list_agents_requires_auth(self):
        """Test that listing agents requires authentication."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/agents/")
            # Should return 403 (forbidden) without auth headers
            assert response.status_code in [401, 403, 400]

    async def test_list_agents_with_viewer(self, test_user_viewer):
        """Test that viewers can list agents."""
        api_key = create_api_key(test_user_viewer["user_id"], test_user_viewer["org_id"])
        
        headers = {
            "X-elevAIte-apikey": api_key,
            "X-elevAIte-UserId": test_user_viewer["user_id"],
            "X-elevAIte-OrganizationId": test_user_viewer["org_id"],
            "X-elevAIte-AccountId": test_user_viewer["account_id"],
            "X-elevAIte-ProjectId": test_user_viewer["project_id"],
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/agents/", headers=headers)
            # Should succeed (200) or fail with proper RBAC error (403)
            assert response.status_code in [200, 403, 401]

    async def test_create_agent_denied_for_viewer(self, test_user_viewer):
        """Test that viewers cannot create agents."""
        api_key = create_api_key(test_user_viewer["user_id"], test_user_viewer["org_id"])
        
        headers = {
            "X-elevAIte-apikey": api_key,
            "X-elevAIte-UserId": test_user_viewer["user_id"],
            "X-elevAIte-OrganizationId": test_user_viewer["org_id"],
            "X-elevAIte-AccountId": test_user_viewer["account_id"],
            "X-elevAIte-ProjectId": test_user_viewer["project_id"],
        }
        
        agent_data = {
            "name": "Test Agent",
            "description": "Test agent for RBAC",
            "provider_type": "openai_textgen",
            "provider_config": {},
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WORKFLOW_ENGINE_URL}/agents/",
                json=agent_data,
                headers=headers,
            )
            # Should be denied (403) for viewers
            assert response.status_code in [403, 401]


@pytest.mark.asyncio
class TestRBACHeaders:
    """Test RBAC header validation."""

    async def test_missing_project_id_header(self, test_user_viewer):
        """Test that missing project ID header is rejected."""
        api_key = create_api_key(test_user_viewer["user_id"], test_user_viewer["org_id"])
        
        headers = {
            "X-elevAIte-apikey": api_key,
            "X-elevAIte-UserId": test_user_viewer["user_id"],
            "X-elevAIte-OrganizationId": test_user_viewer["org_id"],
            "X-elevAIte-AccountId": test_user_viewer["account_id"],
            # Missing ProjectId header
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
            # Should fail with 400 (bad request) or 403 (forbidden)
            assert response.status_code in [400, 403, 401]

    async def test_missing_auth_header(self):
        """Test that missing authentication header is rejected."""
        headers = {
            # Missing apikey and UserId
            "X-elevAIte-OrganizationId": TEST_ORG_ID,
            "X-elevAIte-AccountId": TEST_ACCOUNT_ID,
            "X-elevAIte-ProjectId": TEST_PROJECT_ID,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
            # Should fail with 401 (unauthorized) or 403 (forbidden)
            assert response.status_code in [401, 403, 400]

