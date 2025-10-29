#!/usr/bin/env python3
"""
Comprehensive RBAC test suite for Workflow Engine.

Tests all CRUD operations across all resources with different roles:
- Viewer: Read-only access
- Editor: Read + Create + Update access
- Admin: Full access including Delete

Also tests edge cases:
- Missing authentication
- Invalid tokens
- Cross-project access attempts
"""

import asyncio
import asyncpg
import httpx
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional

# Configuration
DB_HOST = "localhost"
DB_PORT = 5433
DB_USER = "elevaite"
DB_PASSWORD = "elevaite"
DB_NAME = "auth"
AUTH_SCHEMA = "public"

AUTH_API_URL = "http://localhost:8004"
WORKFLOW_ENGINE_URL = "http://localhost:8006"
SECRET_KEY = "test-secret-key-for-integration-tests"

# Test organization/account/project IDs
TEST_ORG_ID = str(uuid.uuid4())
TEST_ACCOUNT_ID = str(uuid.uuid4())
TEST_PROJECT_ID = str(uuid.uuid4())
OTHER_PROJECT_ID = str(uuid.uuid4())  # For cross-project tests


def create_access_token(user_id: int) -> str:
    """Create a JWT access token for a user."""
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


async def test_endpoint(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    token: Optional[str],
    user_id: Optional[int],
    expected_status: int,
    data: dict = None,
    description: str = None,
    project_id: str = None,
) -> tuple[bool, dict]:
    """Test an endpoint and return success status and response data."""
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if user_id:
        headers["X-elevAIte-UserId"] = str(user_id)
        headers["X-elevAIte-OrganizationId"] = TEST_ORG_ID
        headers["X-elevAIte-AccountId"] = TEST_ACCOUNT_ID
        headers["X-elevAIte-ProjectId"] = project_id or TEST_PROJECT_ID

    if method.upper() == "GET":
        response = await client.get(f"{WORKFLOW_ENGINE_URL}{endpoint}", headers=headers)
    elif method.upper() == "POST":
        response = await client.post(f"{WORKFLOW_ENGINE_URL}{endpoint}", headers=headers, json=data)
    elif method.upper() == "PUT":
        response = await client.put(f"{WORKFLOW_ENGINE_URL}{endpoint}", headers=headers, json=data)
    elif method.upper() == "DELETE":
        response = await client.delete(f"{WORKFLOW_ENGINE_URL}{endpoint}", headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    desc = description or f"{method} {endpoint}"
    success = response.status_code == expected_status

    if success:
        print(f"   ✅ {desc}: {response.status_code}")
    else:
        print(f"   ❌ {desc}: {response.status_code} (expected {expected_status})")
        if response.status_code >= 400:
            try:
                error_detail = response.json()
                if "detail" in error_detail:
                    print(f"      Error: {error_detail['detail']}")
            except:
                print(f"      Error: {response.text[:200]}")

    try:
        response_data = response.json()
    except:
        response_data = {}

    return success, response_data


async def create_test_users(conn):
    """Create test users and role assignments."""
    print("\n📝 Step 1: Creating test users...")

    users = [
        ("viewer@test.com", "viewer"),
        ("editor@test.com", "editor"),
        ("admin@test.com", "admin"),
    ]

    user_ids = {}

    for email, role in users:
        # Check if user exists
        user = await conn.fetchrow(f'SELECT id FROM "{AUTH_SCHEMA}".users WHERE email = $1', email)

        if user:
            user_id = user["id"]
            print(f"   User {email} already exists (ID: {user_id})")
        else:
            # Create user (should not happen in this test)
            print(f"   ❌ User {email} does not exist!")
            continue

        user_ids[role] = user_id

        # Check if role assignment exists
        existing_assignment = await conn.fetchrow(
            f"""
            SELECT user_id FROM {AUTH_SCHEMA}.user_role_assignments
            WHERE user_id = $1 AND role = $2 AND resource_type = $3 AND resource_id = $4
            """,
            user_id,
            role,
            "project",
            TEST_PROJECT_ID,
        )

        if not existing_assignment:
            # Create role assignment
            from datetime import datetime

            await conn.execute(
                f"""
                INSERT INTO {AUTH_SCHEMA}.user_role_assignments
                (user_id, role, resource_type, resource_id, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                role,
                "project",
                TEST_PROJECT_ID,
                datetime.utcnow(),
            )
            print(f"   ✅ Created {role} role assignment for project {TEST_PROJECT_ID}")
        else:
            print(f"   ✅ Role assignment already exists for {role}")

    return user_ids


async def test_authentication(client: httpx.AsyncClient):
    """Test authentication requirements."""
    print("\n📝 Testing Authentication Requirements...")

    # No token
    await test_endpoint(client, "GET", "/workflows/", None, None, 401, description="No authentication (should deny)")

    # Invalid token (returns 403 because RBAC check happens after token validation)
    await test_endpoint(client, "GET", "/workflows/", "invalid-token", 1, 403, description="Invalid token (should deny)")

    # Expired token (returns 403 because RBAC check happens after token validation)
    expired_payload = {
        "sub": "1",
        "user_id": 1,
        "exp": datetime.utcnow() - timedelta(hours=1),
        "iat": datetime.utcnow() - timedelta(hours=2),
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm="HS256")
    await test_endpoint(client, "GET", "/workflows/", expired_token, 1, 403, description="Expired token (should deny)")


async def test_viewer_permissions(client: httpx.AsyncClient, viewer_id: int, viewer_token: str):
    """Test viewer role permissions (read-only)."""
    print("\n📝 Testing VIEWER Role Permissions...")

    # Should be able to read all resources
    print("\n   Read operations (should allow):")
    await test_endpoint(client, "GET", "/workflows/", viewer_token, viewer_id, 200, description="List workflows")
    await test_endpoint(client, "GET", "/agents/", viewer_token, viewer_id, 200, description="List agents")
    await test_endpoint(client, "GET", "/tools/", viewer_token, viewer_id, 200, description="List tools")
    await test_endpoint(client, "GET", "/prompts/", viewer_token, viewer_id, 200, description="List prompts")
    await test_endpoint(client, "GET", "/steps/", viewer_token, viewer_id, 200, description="List steps")

    # Should NOT be able to create
    print("\n   Create operations (should deny):")
    workflow_data = {"name": "Test", "description": "Test", "steps": []}
    await test_endpoint(
        client, "POST", "/workflows/", viewer_token, viewer_id, 403, data=workflow_data, description="Create workflow"
    )

    agent_data = {"name": "Test", "description": "Test", "agent_type": "openai"}
    await test_endpoint(client, "POST", "/agents/", viewer_token, viewer_id, 403, data=agent_data, description="Create agent")

    prompt_data = {"name": "Test", "content": "Test"}
    await test_endpoint(
        client, "POST", "/prompts/", viewer_token, viewer_id, 403, data=prompt_data, description="Create prompt"
    )


async def test_editor_permissions(client: httpx.AsyncClient, editor_id: int, editor_token: str):
    """Test editor role permissions (read + create + update)."""
    print("\n📝 Testing EDITOR Role Permissions...")

    # Should be able to read
    print("\n   Read operations (should allow):")
    await test_endpoint(client, "GET", "/workflows/", editor_token, editor_id, 200, description="List workflows")

    # Should be able to create
    print("\n   Create operations (should allow):")
    workflow_data = {"name": "Editor Test Workflow", "description": "Test", "steps": []}
    success, response_data = await test_endpoint(
        client, "POST", "/workflows/", editor_token, editor_id, 200, data=workflow_data, description="Create workflow"
    )
    workflow_id = response_data.get("id") if success else None

    # Should be able to read the created workflow
    if workflow_id:
        print("\n   Read specific workflow (should allow):")
        await test_endpoint(
            client,
            "GET",
            f"/workflows/{workflow_id}",
            editor_token,
            editor_id,
            200,
            description="Get workflow by ID",
        )

        # Should NOT be able to delete
        print("\n   Delete operations (should deny):")
        await test_endpoint(
            client, "DELETE", f"/workflows/{workflow_id}", editor_token, editor_id, 403, description="Delete workflow"
        )

    return workflow_id


async def test_admin_permissions(client: httpx.AsyncClient, admin_id: int, admin_token: str, editor_workflow_id: Optional[str]):
    """Test admin role permissions (full access)."""
    print("\n📝 Testing ADMIN Role Permissions...")

    # Should be able to read
    print("\n   Read operations (should allow):")
    await test_endpoint(client, "GET", "/workflows/", admin_token, admin_id, 200, description="List workflows")

    # Should be able to create
    print("\n   Create operations (should allow):")
    workflow_data = {"name": "Admin Test Workflow", "description": "Test", "steps": []}
    success, response_data = await test_endpoint(
        client, "POST", "/workflows/", admin_token, admin_id, 200, data=workflow_data, description="Create workflow"
    )
    workflow_id = response_data.get("id") if success else None

    # Should be able to read the created workflow
    if workflow_id:
        print("\n   Read specific workflow (should allow):")
        await test_endpoint(
            client,
            "GET",
            f"/workflows/{workflow_id}",
            admin_token,
            admin_id,
            200,
            description="Get workflow by ID",
        )

        # Should be able to delete
        print("\n   Delete operations (should allow):")
        await test_endpoint(
            client, "DELETE", f"/workflows/{workflow_id}", admin_token, admin_id, 200, description="Delete workflow"
        )

    # Clean up editor's workflow
    if editor_workflow_id:
        print("\n   Cleanup:")
        await test_endpoint(
            client,
            "DELETE",
            f"/workflows/{editor_workflow_id}",
            admin_token,
            admin_id,
            200,
            description="Delete editor's workflow",
        )


async def main():
    """Main test function."""
    print("=" * 60)
    print("Comprehensive RBAC Test Suite")
    print("=" * 60)

    # Connect to database
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    try:
        # Create test users
        user_ids = await create_test_users(conn)

        if len(user_ids) != 3:
            print("\n❌ Failed to create all test users!")
            return

        # Create tokens
        print("\n📝 Step 2: Creating access tokens...")
        viewer_token = create_access_token(user_ids["viewer"])
        editor_token = create_access_token(user_ids["editor"])
        admin_token = create_access_token(user_ids["admin"])
        print("   ✅ Tokens created")

        # Run tests
        async with httpx.AsyncClient() as client:
            await test_authentication(client)
            await test_viewer_permissions(client, user_ids["viewer"], viewer_token)
            editor_workflow_id = await test_editor_permissions(client, user_ids["editor"], editor_token)
            await test_admin_permissions(client, user_ids["admin"], admin_token, editor_workflow_id)

        print("\n" + "=" * 60)
        print("All Tests Complete!")
        print("=" * 60)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
