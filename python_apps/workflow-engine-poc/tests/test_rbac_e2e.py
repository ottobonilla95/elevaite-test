"""
End-to-end RBAC integration tests for workflow-engine-poc.

These tests create real users, organizations, accounts, projects, and role assignments
via the Auth API, then test that RBAC guards properly protect workflow-engine-poc endpoints.

Requirements:
- Auth API running on port 8004
- OPA running on port 8181
- PostgreSQL running on port 5434 (for Auth API)
- PostgreSQL running on port 5433 (for workflow-engine-poc)
- Workflow Engine PoC running on port 8006

These tests are designed to run in CI with all services started via docker-compose.
"""

import os
import pytest
import httpx
import asyncpg
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from jose import jwt


# Enable local JWT validation for API keys in RBAC SDK
os.environ["RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["API_KEY_SECRET"] = "test-secret-key-for-integration-tests"
os.environ["ALGORITHM"] = "HS256"

# Test configuration
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://localhost:8004")
WORKFLOW_ENGINE_URL = os.getenv("WORKFLOW_ENGINE_URL", "http://localhost:8006")
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-do-not-use-in-production")
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "test-secret-key-for-integration-tests")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Database config for Auth API
AUTH_DB_HOST = os.getenv("AUTH_DB_HOST", "localhost")
AUTH_DB_PORT = int(os.getenv("AUTH_DB_PORT", "5434"))
AUTH_DB_USER = os.getenv("AUTH_DB_USER", "auth_user")
AUTH_DB_PASSWORD = os.getenv("AUTH_DB_PASSWORD", "auth_password")
AUTH_DB_NAME = os.getenv("AUTH_DB_NAME", "auth_db")


@pytest.fixture(scope="session")
async def http_client() -> httpx.AsyncClient:
    """Create an async HTTP client for making requests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def superuser(http_client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Create a superuser for test setup.

    Returns:
        Dict with user info including id, email, access_token
    """
    # Register a test user
    timestamp = datetime.now(timezone.utc).timestamp()
    email = f"superuser-{timestamp}@test.elevaite.com"

    response = await http_client.post(
        f"{AUTH_API_URL}/api/auth/register", json={"email": email, "password": "SuperSecure123!", "full_name": "Test Superuser"}
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create superuser: {response.status_code} - {response.text}")

    user_data = response.json()

    # Make the user a superuser by directly updating the database
    conn = await asyncpg.connect(
        host=AUTH_DB_HOST,
        port=AUTH_DB_PORT,
        user=AUTH_DB_USER,
        password=AUTH_DB_PASSWORD,
        database=AUTH_DB_NAME,
    )
    try:
        await conn.execute("UPDATE users SET is_superuser = true WHERE id = $1", user_data["id"])
    finally:
        await conn.close()

    # Create an access token
    access_token = jwt.encode(
        {
            "sub": str(user_data["id"]),
            "type": "access",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "id": user_data["id"],
        "email": email,
        "access_token": access_token,
        "is_superuser": True,
    }


@pytest.fixture
async def test_organization(http_client: httpx.AsyncClient, superuser: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a test organization.

    Returns:
        Dict with organization info (id, name)
    """
    timestamp = datetime.now(timezone.utc).timestamp()
    org_name = f"Test Org {timestamp}"

    response = await http_client.post(
        f"{AUTH_API_URL}/api/rbac/organizations",
        json={"name": org_name, "description": "Test organization for RBAC E2E tests"},
        headers={"Authorization": f"Bearer {superuser['access_token']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create organization: {response.status_code} - {response.text}")

    org_data = response.json()
    return {"id": org_data["id"], "name": org_data["name"]}


@pytest.fixture
async def test_account(
    http_client: httpx.AsyncClient, superuser: Dict[str, Any], test_organization: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a test account within the organization.

    Returns:
        Dict with account info (id, name, organization_id)
    """
    timestamp = datetime.now(timezone.utc).timestamp()
    account_name = f"Test Account {timestamp}"

    response = await http_client.post(
        f"{AUTH_API_URL}/api/rbac/accounts",
        json={
            "name": account_name,
            "description": "Test account for RBAC E2E tests",
            "organization_id": test_organization["id"],
        },
        headers={"Authorization": f"Bearer {superuser['access_token']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create account: {response.status_code} - {response.text}")

    account_data = response.json()
    return {
        "id": account_data["id"],
        "name": account_data["name"],
        "organization_id": test_organization["id"],
    }


@pytest.fixture
async def test_project(
    http_client: httpx.AsyncClient, superuser: Dict[str, Any], test_account: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a test project within the account.

    Returns:
        Dict with project info (id, name, account_id, organization_id)
    """
    timestamp = datetime.now(timezone.utc).timestamp()
    project_name = f"Test Project {timestamp}"

    response = await http_client.post(
        f"{AUTH_API_URL}/api/rbac/projects",
        json={
            "name": project_name,
            "description": "Test project for RBAC E2E tests",
            "account_id": test_account["id"],
            "organization_id": test_account["organization_id"],  # Add organization_id
        },
        headers={"Authorization": f"Bearer {superuser['access_token']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create project: {response.status_code} - {response.text}")

    project_data = response.json()
    return {
        "id": project_data["id"],
        "name": project_data["name"],
        "account_id": test_account["id"],
        "organization_id": test_account["organization_id"],
    }


async def create_user_with_role(
    http_client: httpx.AsyncClient,
    superuser: Dict[str, Any],
    role: str,
    project: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Helper to create a user with a specific role assignment.

    Args:
        http_client: HTTP client
        superuser: Superuser credentials
        role: Role to assign (viewer, editor, admin)
        project: Project info

    Returns:
        Dict with user info including id, email, access_token, role
    """
    # Register a test user
    timestamp = datetime.now(timezone.utc).timestamp()
    email = f"test-{role}-{timestamp}@test.elevaite.com"

    response = await http_client.post(
        f"{AUTH_API_URL}/api/auth/register",
        json={"email": email, "password": "TestPassword123!", "full_name": f"Test {role.title()} User"},
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Could not create user: {response.status_code} - {response.text}")

    user_data = response.json()

    # Create role assignment
    # Admin roles are assigned at account level, other roles at project level
    if role == "admin":
        resource_type = "account"
        resource_id = project["account_id"]
    else:
        resource_type = "project"
        resource_id = project["id"]

    response = await http_client.post(
        f"{AUTH_API_URL}/api/rbac/user_role_assignments",
        json={
            "user_id": user_data["id"],
            "role": role,
            "resource_type": resource_type,
            "resource_id": resource_id,
        },
        headers={"Authorization": f"Bearer {superuser['access_token']}"},
    )

    if response.status_code not in (200, 201):
        raise Exception(f"Could not create role assignment: {response.status_code} - {response.text}")

    # Create an API key token (not an access token)
    # API keys use type="api_key" and are validated with API_KEY_SECRET
    api_key = jwt.encode(
        {
            "sub": str(user_data["id"]),
            "type": "api_key",
            "organization_id": project["organization_id"],
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        },
        API_KEY_SECRET,
        algorithm=ALGORITHM,
    )

    return {
        "id": user_data["id"],
        "email": email,
        "access_token": api_key,  # Keep the field name for compatibility
        "role": role,
    }


@pytest.fixture
async def viewer_user(
    http_client: httpx.AsyncClient, superuser: Dict[str, Any], test_project: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a user with viewer role."""
    return await create_user_with_role(http_client, superuser, "viewer", test_project)


@pytest.fixture
async def editor_user(
    http_client: httpx.AsyncClient, superuser: Dict[str, Any], test_project: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a user with editor role."""
    return await create_user_with_role(http_client, superuser, "editor", test_project)


@pytest.fixture
async def admin_user(http_client: httpx.AsyncClient, superuser: Dict[str, Any], test_project: Dict[str, Any]) -> Dict[str, Any]:
    """Create a user with admin role."""
    return await create_user_with_role(http_client, superuser, "admin", test_project)


def make_rbac_headers(user: Dict[str, Any], project: Dict[str, Any]) -> Dict[str, str]:
    """
    Create RBAC headers for API requests.

    Args:
        user: User info with access_token
        project: Project info with id, account_id, organization_id

    Returns:
        Dict of headers for RBAC
    """
    return {
        "X-elevAIte-apikey": user["access_token"],
        "X-elevAIte-UserId": str(user["id"]),
        "X-elevAIte-OrganizationId": project["organization_id"],
        "X-elevAIte-AccountId": project["account_id"],
        "X-elevAIte-ProjectId": project["id"],
    }


@pytest.mark.asyncio
class TestWorkflowEndpointsRBAC:
    """Test RBAC enforcement on workflow endpoints."""

    async def test_list_workflows_no_auth_denied(self, http_client: httpx.AsyncClient):
        """Test that listing workflows without authentication is denied."""
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/")
        assert response.status_code in [401, 403, 400], f"Expected 401/403/400, got {response.status_code}"

    async def test_list_workflows_viewer_allowed(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that viewers can list workflows."""
        headers = make_rbac_headers(viewer_user, test_project)
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert isinstance(response.json(), list), "Expected list of workflows"

    async def test_list_workflows_editor_allowed(
        self, http_client: httpx.AsyncClient, editor_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that editors can list workflows."""
        headers = make_rbac_headers(editor_user, test_project)
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    async def test_list_workflows_admin_allowed(
        self, http_client: httpx.AsyncClient, admin_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that admins can list workflows."""
        headers = make_rbac_headers(admin_user, test_project)
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    async def test_create_workflow_viewer_denied(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that viewers cannot create workflows."""
        headers = make_rbac_headers(viewer_user, test_project)
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test workflow for RBAC",
            "steps": [],
            "connections": [],
        }
        response = await http_client.post(f"{WORKFLOW_ENGINE_URL}/workflows/", json=workflow_data, headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

    async def test_create_workflow_editor_allowed(
        self, http_client: httpx.AsyncClient, editor_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that editors can create workflows."""
        headers = make_rbac_headers(editor_user, test_project)
        workflow_data = {
            "name": "Test Workflow by Editor",
            "description": "Test workflow created by editor",
            "steps": [],
            "connections": [],
        }
        response = await http_client.post(f"{WORKFLOW_ENGINE_URL}/workflows/", json=workflow_data, headers=headers)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

    async def test_create_workflow_admin_allowed(
        self, http_client: httpx.AsyncClient, admin_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that admins can create workflows."""
        headers = make_rbac_headers(admin_user, test_project)
        workflow_data = {
            "name": "Test Workflow by Admin",
            "description": "Test workflow created by admin",
            "steps": [],
            "connections": [],
        }
        response = await http_client.post(f"{WORKFLOW_ENGINE_URL}/workflows/", json=workflow_data, headers=headers)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"


@pytest.mark.asyncio
class TestExecutionEndpointsRBAC:
    """Test RBAC enforcement on execution endpoints."""

    async def test_list_executions_no_auth_denied(self, http_client: httpx.AsyncClient):
        """Test that listing executions without authentication is denied."""
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/executions/")
        assert response.status_code in [401, 403, 400], f"Expected 401/403/400, got {response.status_code}"

    async def test_list_executions_viewer_allowed(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that viewers can list executions."""
        headers = make_rbac_headers(viewer_user, test_project)
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/executions/", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    async def test_list_executions_editor_allowed(
        self, http_client: httpx.AsyncClient, editor_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that editors can list executions."""
        headers = make_rbac_headers(editor_user, test_project)
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/executions/", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


@pytest.mark.asyncio
class TestAgentEndpointsRBAC:
    """Test RBAC enforcement on agent endpoints."""

    async def test_list_agents_no_auth_denied(self, http_client: httpx.AsyncClient):
        """Test that listing agents without authentication is denied."""
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/agents/")
        assert response.status_code in [401, 403, 400], f"Expected 401/403/400, got {response.status_code}"

    async def test_list_agents_viewer_allowed(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that viewers can list agents."""
        headers = make_rbac_headers(viewer_user, test_project)
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/agents/", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    async def test_create_agent_viewer_denied(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that viewers cannot create agents."""
        headers = make_rbac_headers(viewer_user, test_project)
        timestamp = datetime.now(timezone.utc).timestamp()
        agent_data = {
            "name": f"Test Agent {timestamp}",
            "description": "Test agent for RBAC",
            "provider_type": "openai_textgen",
            "provider_config": {},
            "system_prompt_id": "00000000-0000-0000-0000-000000000000",  # Dummy UUID
        }
        response = await http_client.post(f"{WORKFLOW_ENGINE_URL}/agents/", json=agent_data, headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

    async def test_create_agent_editor_allowed(
        self, http_client: httpx.AsyncClient, editor_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that editors can create agents."""
        headers = make_rbac_headers(editor_user, test_project)
        timestamp = datetime.now(timezone.utc).timestamp()
        agent_data = {
            "name": f"Test Agent by Editor {timestamp}",
            "description": "Test agent created by editor",
            "provider_type": "openai_textgen",
            "provider_config": {},
            "system_prompt_id": "00000000-0000-0000-0000-000000000000",  # Dummy UUID
        }
        response = await http_client.post(f"{WORKFLOW_ENGINE_URL}/agents/", json=agent_data, headers=headers)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"


@pytest.mark.asyncio
class TestRBACHeaderValidation:
    """Test RBAC header validation."""

    async def test_missing_project_id_denied(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that missing project ID header is denied."""
        headers = {
            "X-elevAIte-apikey": viewer_user["access_token"],
            "X-elevAIte-UserId": str(viewer_user["id"]),
            "X-elevAIte-OrganizationId": test_project["organization_id"],
            "X-elevAIte-AccountId": test_project["account_id"],
            # Missing ProjectId
        }
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
        assert response.status_code in [400, 403, 401], f"Expected 400/403/401, got {response.status_code}"

    async def test_missing_account_id_allowed_for_project_roles(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that missing account ID header is allowed for project-level roles (viewer/editor).

        The account_id header is optional for project-scoped checks because the role assignment
        is at the project level. Admin roles (assigned at account level) would fail without account_id.
        """
        headers = {
            "X-elevAIte-apikey": viewer_user["access_token"],
            "X-elevAIte-UserId": str(viewer_user["id"]),
            "X-elevAIte-OrganizationId": test_project["organization_id"],
            "X-elevAIte-ProjectId": test_project["id"],
            # Missing AccountId - should still work for project-level roles
        }
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
        assert response.status_code == 200, f"Expected 200 for project-level role, got {response.status_code}: {response.text}"

    async def test_missing_org_id_denied(
        self, http_client: httpx.AsyncClient, viewer_user: Dict[str, Any], test_project: Dict[str, Any]
    ):
        """Test that missing organization ID header is denied."""
        headers = {
            "X-elevAIte-apikey": viewer_user["access_token"],
            "X-elevAIte-UserId": str(viewer_user["id"]),
            "X-elevAIte-AccountId": test_project["account_id"],
            "X-elevAIte-ProjectId": test_project["id"],
            # Missing OrganizationId
        }
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
        assert response.status_code in [400, 403, 401], f"Expected 400/403/401, got {response.status_code}"

    async def test_missing_auth_denied(self, http_client: httpx.AsyncClient, test_project: Dict[str, Any]):
        """Test that missing authentication is denied."""
        headers = {
            # Missing apikey and UserId
            "X-elevAIte-OrganizationId": test_project["organization_id"],
            "X-elevAIte-AccountId": test_project["account_id"],
            "X-elevAIte-ProjectId": test_project["id"],
        }
        response = await http_client.get(f"{WORKFLOW_ENGINE_URL}/workflows/", headers=headers)
        assert response.status_code in [401, 403, 400], f"Expected 401/403/400, got {response.status_code}"
