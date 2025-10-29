"""Fixtures for integration tests with real Auth API and RBAC service."""

import os
import uuid
import pytest
import httpx
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from jose import jwt


# Environment variables for integration tests
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://localhost:8004")
OPA_URL = os.getenv("OPA_URL", "http://localhost:8181")
# Use SECRET_KEY for access tokens (not API_KEY_SECRET which is for API keys)
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-do-not-use-in-production")
# Use API_KEY_SECRET for API keys (type="api_key")
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "test-secret-key-for-integration-tests")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


@pytest.fixture(scope="session")
def auth_api_url() -> str:
    """Return the Auth API base URL."""
    return AUTH_API_URL


@pytest.fixture(scope="session")
def opa_url() -> str:
    """Return the OPA base URL."""
    return OPA_URL


@pytest.fixture(scope="session")
def api_key_config() -> Dict[str, str]:
    """Return API key configuration."""
    return {
        "secret": SECRET_KEY,
        "algorithm": ALGORITHM,
    }


@pytest.fixture
async def http_client() -> httpx.AsyncClient:
    """Create an async HTTP client for making requests."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client


@pytest.fixture
def create_test_jwt():
    """Factory fixture to create test JWT tokens."""

    def _create_jwt(user_id: str, token_type: str = "api_key", expires_in_minutes: int = 60, **extra_claims) -> str:
        """
        Create a test JWT token.

        Args:
            user_id: User ID to include in 'sub' claim
            token_type: Token type (default: 'api_key')
            expires_in_minutes: Expiration time in minutes
            **extra_claims: Additional claims to include

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=expires_in_minutes)

        payload = {"sub": str(user_id), "type": token_type, "exp": exp, "iat": now, **extra_claims}

        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return _create_jwt


@pytest.fixture
async def test_user_active(http_client: httpx.AsyncClient, auth_api_url: str) -> Dict[str, Any]:
    """
    Create an active test user via Auth API and make them a superuser.

    Returns:
        Dict with user info including id, email, api_key
    """
    # Register a test user
    register_url = f"{auth_api_url}/api/auth/register"
    timestamp = datetime.now(timezone.utc).timestamp()
    email = f"test-active-{timestamp}@example.com"

    response = await http_client.post(
        register_url, json={"email": email, "password": "SecurePass123!", "full_name": "Test Active User"}
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test user: {response.status_code} - {response.text}")

    user_data = response.json()

    # Make the user a superuser by directly updating the database
    # This is a test-only operation
    import asyncpg

    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="elevaite",
        password="elevaite",
        database="auth",
    )
    try:
        await conn.execute("UPDATE users SET is_superuser = true WHERE id = $1", user_data["id"])
    finally:
        await conn.close()

    # Create an access token for this user
    # Use SECRET_KEY (not API_KEY_SECRET) because verify_token uses settings.SECRET_KEY
    api_key = jwt.encode(
        {
            "sub": str(user_data["id"]),
            "type": "access",  # Access token type
            "tenant_id": "default",  # Add tenant_id claim
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "status": user_data.get("status", "active"),
        "is_superuser": True,
        "api_key": api_key,
    }


@pytest.fixture
async def test_user_with_api_key(http_client: httpx.AsyncClient, auth_api_url: str) -> Dict[str, Any]:
    """
    Create an active test user with a real API key (type="api_key").

    Returns:
        Dict with user info including id, email, api_key (JWT with type="api_key")
    """
    # Register a test user
    register_url = f"{auth_api_url}/api/auth/register"
    timestamp = datetime.now(timezone.utc).timestamp()
    email = f"test-apikey-{timestamp}@example.com"

    response = await http_client.post(
        register_url, json={"email": email, "password": "SecurePass123!", "full_name": "Test API Key User"}
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test user: {response.status_code} - {response.text}")

    user_data = response.json()

    # Create an API key for this user
    # Use API_KEY_SECRET because validate-apikey uses settings.API_KEY_SECRET
    api_key = jwt.encode(
        {
            "sub": str(user_data["id"]),
            "type": "api_key",  # API key type (not "access")
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        },
        API_KEY_SECRET,
        algorithm=ALGORITHM,
    )

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "status": user_data.get("status", "active"),
        "api_key": api_key,
    }


@pytest.fixture
async def test_user_no_assignments(http_client: httpx.AsyncClient, auth_api_url: str) -> Dict[str, Any]:
    """
    Create an active test user with NO role assignments.

    Returns:
        Dict with user info including id, email, api_key
    """
    # Register a test user
    register_url = f"{auth_api_url}/api/auth/register"
    timestamp = datetime.now(timezone.utc).timestamp()
    email = f"test-no-assignments-{timestamp}@example.com"

    response = await http_client.post(
        register_url, json={"email": email, "password": "SecurePass123!", "full_name": "Test No Assignments User"}
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test user: {response.status_code} - {response.text}")

    user_data = response.json()

    # Create an access token for this user
    api_key = jwt.encode(
        {
            "sub": str(user_data["id"]),
            "type": "access",
            "tenant_id": "default",
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "status": user_data.get("status", "active"),
        "is_superuser": False,
        "api_key": api_key,
    }


@pytest.fixture
async def test_user_inactive(http_client: httpx.AsyncClient, auth_api_url: str) -> Dict[str, Any]:
    """
    Create an inactive test user.

    Note: This requires admin access to set user status to inactive.
    For now, we'll skip this if we can't create inactive users.

    Returns:
        Dict with user info including id, email, api_key
    """
    # This would require admin API access to create an inactive user
    # For now, we'll return a mock user and skip tests that need it
    pytest.skip("Creating inactive users requires admin API access")


@pytest.fixture
async def test_organization(
    http_client: httpx.AsyncClient, auth_api_url: str, test_user_active: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a test organization via Auth API.

    Returns:
        Dict with organization info (id, name)
    """
    # Create organization via Auth API
    org_url = f"{auth_api_url}/api/rbac/organizations"
    org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}

    response = await http_client.post(
        org_url,
        json=org_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test organization: {response.status_code} - {response.text}")

    org = response.json()
    return {"id": org["id"], "name": org["name"]}


@pytest.fixture
async def test_account(
    http_client: httpx.AsyncClient, auth_api_url: str, test_organization: Dict[str, Any], test_user_active: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a test account via Auth API.

    Returns:
        Dict with account info
    """
    # Create account via Auth API
    account_url = f"{auth_api_url}/api/rbac/accounts"
    account_data = {"name": f"Test Account {uuid.uuid4().hex[:8]}", "organization_id": test_organization["id"]}

    response = await http_client.post(
        account_url,
        json=account_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test account: {response.status_code} - {response.text}")

    account = response.json()
    return {"id": account["id"], "name": account["name"], "organization_id": account["organization_id"]}


@pytest.fixture
async def test_project(
    http_client: httpx.AsyncClient,
    auth_api_url: str,
    test_organization: Dict[str, Any],
    test_account: Dict[str, Any],
    test_user_active: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a test project via Auth API.

    Returns:
        Dict with project info
    """
    # Create project via Auth API
    project_url = f"{auth_api_url}/api/rbac/projects"
    project_data = {
        "name": f"Test Project {uuid.uuid4().hex[:8]}",
        "organization_id": test_organization["id"],
        "account_id": test_account["id"],
    }

    response = await http_client.post(
        project_url,
        json=project_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test project: {response.status_code} - {response.text}")

    project = response.json()
    return {
        "id": project["id"],
        "name": project["name"],
        "organization_id": project["organization_id"],
        "account_id": project["account_id"],
    }


@pytest.fixture
async def test_role_assignment(
    http_client: httpx.AsyncClient, auth_api_url: str, test_user_active: Dict[str, Any], test_project: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a test role assignment.

    This would assign a role to the test user for the test project.
    For now, we'll return mock data.

    Returns:
        Dict with role assignment info
    """
    return {"user_id": test_user_active["id"], "role": "editor", "resource_type": "project", "resource_id": test_project["id"]}


@pytest.fixture
async def check_auth_api_available(http_client: httpx.AsyncClient, auth_api_url: str) -> bool:
    """
    Check if Auth API is available.

    Skips tests if Auth API is not running.
    """
    try:
        response = await http_client.get(f"{auth_api_url}/api/health", timeout=2.0)
        if response.status_code != 200:
            pytest.skip(f"Auth API not available at {auth_api_url}")
        return True
    except Exception as e:
        pytest.skip(f"Auth API not available at {auth_api_url}: {e}")


@pytest.fixture
async def check_opa_available(http_client: httpx.AsyncClient, opa_url: str) -> bool:
    """
    Check if OPA is available.

    Skips tests if OPA is not running.
    """
    try:
        response = await http_client.get(f"{opa_url}/health", timeout=2.0)
        if response.status_code != 200:
            pytest.skip(f"OPA not available at {opa_url}")
        return True
    except Exception as e:
        pytest.skip(f"OPA not available at {opa_url}: {e}")


@pytest.fixture(autouse=True)
async def setup_integration_env():
    """
    Set up environment variables for integration tests.

    This runs automatically before each test.
    """
    # Set environment variables
    os.environ["AUTHZ_SERVICE_URL"] = AUTH_API_URL
    os.environ["OPA_URL"] = OPA_URL
    os.environ["SECRET_KEY"] = SECRET_KEY
    os.environ["API_KEY_SECRET"] = API_KEY_SECRET
    os.environ["ALGORITHM"] = ALGORITHM

    yield

    # Cleanup is not needed as we're just setting env vars


# ============================================================================
# RBAC Resource Fixtures (for Phase 1.2: RBAC Service Integration)
# ============================================================================


@pytest.fixture
async def test_project_in_account(
    http_client: httpx.AsyncClient,
    auth_api_url: str,
    test_organization: Dict[str, Any],
    test_account: Dict[str, Any],
    test_user_active: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a test project in a specific account.

    Returns:
        Dict with project info (id, name, organization_id, account_id)
    """
    # Create project via Auth API
    project_url = f"{auth_api_url}/api/rbac/projects"
    project_data = {
        "name": f"Test Project {uuid.uuid4().hex[:8]}",
        "organization_id": test_organization["id"],
        "account_id": test_account["id"],
    }

    response = await http_client.post(
        project_url,
        json=project_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test project: {response.status_code} - {response.text}")

    project = response.json()
    return {
        "id": project["id"],
        "name": project["name"],
        "organization_id": project["organization_id"],
        "account_id": project["account_id"],
    }


# ============================================================================
# Role Assignment Fixtures
# ============================================================================


@pytest.fixture
async def test_viewer_assignment(
    http_client: httpx.AsyncClient,
    auth_api_url: str,
    test_user_active: Dict[str, Any],
    test_project: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assign viewer role to test user on test project.

    Returns:
        Dict with role assignment info
    """
    assignment_url = f"{auth_api_url}/api/rbac/user_role_assignments"
    assignment_data = {
        "user_id": test_user_active["id"],
        "role": "viewer",
        "resource_type": "project",
        "resource_id": test_project["id"],
    }

    response = await http_client.post(
        assignment_url,
        json=assignment_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create role assignment: {response.status_code} - {response.text}")

    return response.json()


@pytest.fixture
async def test_editor_assignment(
    http_client: httpx.AsyncClient,
    auth_api_url: str,
    test_user_active: Dict[str, Any],
    test_project: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assign editor role to test user on test project.

    Returns:
        Dict with role assignment info
    """
    assignment_url = f"{auth_api_url}/api/rbac/user_role_assignments"
    assignment_data = {
        "user_id": test_user_active["id"],
        "role": "editor",
        "resource_type": "project",
        "resource_id": test_project["id"],
    }

    response = await http_client.post(
        assignment_url,
        json=assignment_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create role assignment: {response.status_code} - {response.text}")

    return response.json()


@pytest.fixture
async def test_admin_assignment(
    http_client: httpx.AsyncClient,
    auth_api_url: str,
    test_user_active: Dict[str, Any],
    test_account: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assign admin role to test user on test account.

    Returns:
        Dict with role assignment info
    """
    assignment_url = f"{auth_api_url}/api/rbac/user_role_assignments"
    assignment_data = {
        "user_id": test_user_active["id"],
        "role": "admin",
        "resource_type": "account",
        "resource_id": test_account["id"],
    }

    response = await http_client.post(
        assignment_url,
        json=assignment_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create role assignment: {response.status_code} - {response.text}")

    return response.json()


@pytest.fixture
async def test_superadmin_assignment(
    http_client: httpx.AsyncClient,
    auth_api_url: str,
    test_user_active: Dict[str, Any],
    test_organization: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assign superadmin role to test user on test organization.

    Returns:
        Dict with role assignment info
    """
    assignment_url = f"{auth_api_url}/api/rbac/user_role_assignments"
    assignment_data = {
        "user_id": test_user_active["id"],
        "role": "superadmin",
        "resource_type": "organization",
        "resource_id": test_organization["id"],
    }

    response = await http_client.post(
        assignment_url,
        json=assignment_data,
        headers={"Authorization": f"Bearer {test_user_active['api_key']}"},
    )

    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create role assignment: {response.status_code} - {response.text}")

    return response.json()


@pytest.fixture
async def test_viewer_assignment_inactive(
    http_client: httpx.AsyncClient,
    auth_api_url: str,
    test_user_inactive: Dict[str, Any],
    test_project: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assign viewer role to inactive test user on test project.

    This will be skipped until we can create inactive users.

    Returns:
        Dict with role assignment info
    """
    # This will be skipped by test_user_inactive fixture
    pass
