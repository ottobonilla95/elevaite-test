#!/usr/bin/env python3
"""
Test script to verify granular actions work with real RBAC.

This script:
1. Creates test users with different roles in the database
2. Gets access tokens for each user
3. Tests endpoints with each user to verify permissions
"""

import asyncio
import asyncpg
import httpx
import sys
import os
import uuid
from jose import jwt
from datetime import datetime, timedelta, timezone

# Add auth_api to path to use its security module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "auth_api"))
from app.core.security import get_password_hash

# Configuration
DB_HOST = "localhost"
DB_PORT = 5433
DB_USER = "elevaite"
DB_PASSWORD = "elevaite"
DB_NAME = "auth"
AUTH_SCHEMA = "public"

SECRET_KEY = "test-secret-key-for-integration-tests"
WORKFLOW_ENGINE_URL = "http://localhost:8006"

# Test data - use proper UUIDs
TEST_ORG_ID = str(uuid.uuid4())
TEST_ACCOUNT_ID = str(uuid.uuid4())
TEST_PROJECT_ID = str(uuid.uuid4())


async def create_test_user(email: str, role: str) -> int:
    """Create a test user with a role assignment."""
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    try:
        # Check if user exists
        existing_user = await conn.fetchrow(f"SELECT id FROM {AUTH_SCHEMA}.users WHERE email = $1", email)

        if existing_user:
            user_id = existing_user["id"]
            print(f"   User {email} already exists (ID: {user_id})")
        else:
            # Create user
            hashed_password = get_password_hash("Test123!")
            now = datetime.now(timezone.utc)

            user_id = await conn.fetchval(
                f"""
                INSERT INTO {AUTH_SCHEMA}.users
                (email, hashed_password, full_name, is_verified, is_superuser, created_at, updated_at, status, mfa_enabled, failed_login_attempts)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                email,
                hashed_password,
                f"Test {role.title()}",
                True,
                False,
                now,
                now,
                "active",
                False,
                0,
            )
            print(f"   ✅ Created user: {email} (ID: {user_id})")

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
                datetime.now(timezone.utc),
            )
            print(f"   ✅ Created {role} role assignment for project {TEST_PROJECT_ID}")
        else:
            print("   Role assignment already exists")

        return user_id

    finally:
        await conn.close()


def create_access_token(user_id: int) -> str:
    """Create an access token for a user."""
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


async def test_endpoint(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    token: str,
    user_id: int,
    expected_status: int,
    data: dict = None,
    description: str = None,
) -> bool:
    """Test an endpoint with a token."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-elevAIte-UserId": str(user_id),
        "X-elevAIte-OrganizationId": TEST_ORG_ID,
        "X-elevAIte-AccountId": TEST_ACCOUNT_ID,
        "X-elevAIte-ProjectId": TEST_PROJECT_ID,
    }

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
    if response.status_code == expected_status:
        print(f"   ✅ {desc}: {response.status_code} (expected {expected_status})")
        return True
    else:
        print(f"   ❌ {desc}: {response.status_code} (expected {expected_status})")
        if response.status_code >= 400:
            try:
                error_detail = response.json()
                if "detail" in error_detail:
                    print(f"      Error: {error_detail['detail']}")
                else:
                    print(f"      Error: {error_detail}")
            except:
                print(f"      Error: {response.text[:200]}")
        return False


async def main():
    """Main test function."""
    print("=" * 60)
    print("Testing Granular Actions with Real RBAC")
    print("=" * 60)

    # Create test users
    print("\n📝 Step 1: Creating test users...")
    viewer_id = await create_test_user("viewer@test.com", "viewer")
    editor_id = await create_test_user("editor@test.com", "editor")
    admin_id = await create_test_user("admin@test.com", "admin")

    # Create tokens
    print("\n📝 Step 2: Creating access tokens...")
    viewer_token = create_access_token(viewer_id)
    editor_token = create_access_token(editor_id)
    admin_token = create_access_token(admin_id)
    print("   ✅ Tokens created")

    # Test endpoints
    print("\n📝 Step 3: Testing endpoints...")

    async with httpx.AsyncClient() as client:
        # Test viewer (should only be able to view)
        print("\n   Testing VIEWER role (read-only access):")
        await test_endpoint(client, "GET", "/workflows/", viewer_token, viewer_id, 200, description="List workflows")
        await test_endpoint(client, "GET", "/agents/", viewer_token, viewer_id, 200, description="List agents")
        await test_endpoint(client, "GET", "/tools/", viewer_token, viewer_id, 200, description="List tools")
        await test_endpoint(client, "GET", "/prompts/", viewer_token, viewer_id, 200, description="List prompts")

        # Viewer should NOT be able to create
        print("\n   Testing VIEWER role (should deny create operations):")
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test",
            "steps": [],
        }
        await test_endpoint(
            client,
            "POST",
            "/workflows/",
            viewer_token,
            viewer_id,
            403,
            data=workflow_data,
            description="Create workflow (should deny)",
        )

        agent_data = {
            "name": "Test Agent",
            "description": "Test",
            "agent_type": "openai",
        }
        await test_endpoint(
            client, "POST", "/agents/", viewer_token, viewer_id, 403, data=agent_data, description="Create agent (should deny)"
        )

        # Test editor (should be able to view and create)
        print("\n   Testing EDITOR role (read + create access):")
        await test_endpoint(client, "GET", "/workflows/", editor_token, editor_id, 200, description="List workflows")
        await test_endpoint(client, "GET", "/agents/", editor_token, editor_id, 200, description="List agents")
        await test_endpoint(client, "GET", "/tools/", editor_token, editor_id, 200, description="List tools")

        # Editor should be able to create
        print("\n   Testing EDITOR role (create operations):")
        response = await client.post(
            f"{WORKFLOW_ENGINE_URL}/workflows/",
            headers={
                "Authorization": f"Bearer {editor_token}",
                "X-elevAIte-UserId": str(editor_id),
                "X-elevAIte-OrganizationId": TEST_ORG_ID,
                "X-elevAIte-AccountId": TEST_ACCOUNT_ID,
                "X-elevAIte-ProjectId": TEST_PROJECT_ID,
            },
            json=workflow_data,
        )
        if response.status_code in [200, 201]:
            print(f"   ✅ Create workflow: {response.status_code}")
            created_workflow_id = response.json().get("id")
        else:
            print(f"   ❌ Create workflow: {response.status_code}")
            print(f"      Error: {response.text[:200]}")
            created_workflow_id = None

        # Editor should NOT be able to delete
        if created_workflow_id:
            print("\n   Testing EDITOR role (should deny delete operations):")
            await test_endpoint(
                client,
                "DELETE",
                f"/workflows/{created_workflow_id}",
                editor_token,
                editor_id,
                403,
                description="Delete workflow (should deny)",
            )

        # Test admin (should be able to do everything)
        print("\n   Testing ADMIN role (full access):")
        await test_endpoint(client, "GET", "/workflows/", admin_token, admin_id, 200, description="List workflows")
        await test_endpoint(client, "GET", "/agents/", admin_token, admin_id, 200, description="List agents")
        await test_endpoint(client, "GET", "/tools/", admin_token, admin_id, 200, description="List tools")

        # Admin should be able to create
        print("\n   Testing ADMIN role (create operations):")
        response = await client.post(
            f"{WORKFLOW_ENGINE_URL}/workflows/",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "X-elevAIte-UserId": str(admin_id),
                "X-elevAIte-OrganizationId": TEST_ORG_ID,
                "X-elevAIte-AccountId": TEST_ACCOUNT_ID,
                "X-elevAIte-ProjectId": TEST_PROJECT_ID,
            },
            json=workflow_data,
        )
        if response.status_code in [200, 201]:
            print(f"   ✅ Create workflow: {response.status_code}")
            admin_workflow_id = response.json().get("id")
        else:
            print(f"   ❌ Create workflow: {response.status_code}")
            print(f"      Error: {response.text[:200]}")
            admin_workflow_id = None

        # Admin should be able to delete
        if admin_workflow_id:
            print("\n   Testing ADMIN role (delete operations):")
            await test_endpoint(
                client, "DELETE", f"/workflows/{admin_workflow_id}", admin_token, admin_id, 200, description="Delete workflow"
            )

        # Clean up editor's workflow if it exists
        if created_workflow_id:
            await client.delete(
                f"{WORKFLOW_ENGINE_URL}/workflows/{created_workflow_id}",
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "X-elevAIte-UserId": str(admin_id),
                    "X-elevAIte-OrganizationId": TEST_ORG_ID,
                    "X-elevAIte-AccountId": TEST_ACCOUNT_ID,
                    "X-elevAIte-ProjectId": TEST_PROJECT_ID,
                },
            )

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
