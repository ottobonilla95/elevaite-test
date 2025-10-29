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
            print(f"   Role assignment already exists")

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


async def test_endpoint(client: httpx.AsyncClient, endpoint: str, token: str, user_id: int, expected_status: int) -> bool:
    """Test an endpoint with a token."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-elevAIte-UserId": str(user_id),
        "X-elevAIte-OrganizationId": TEST_ORG_ID,
        "X-elevAIte-AccountId": TEST_ACCOUNT_ID,
        "X-elevAIte-ProjectId": TEST_PROJECT_ID,
    }

    response = await client.get(f"{WORKFLOW_ENGINE_URL}{endpoint}", headers=headers)

    if response.status_code == expected_status:
        print(f"   ✅ {endpoint}: {response.status_code} (expected {expected_status})")
        return True
    else:
        print(f"   ❌ {endpoint}: {response.status_code} (expected {expected_status})")
        if response.status_code >= 400:
            try:
                print(f"      Error: {response.json()}")
            except:
                print(f"      Error: {response.text}")
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
        print("\n   Testing VIEWER role:")
        await test_endpoint(client, "/workflows/", viewer_token, viewer_id, 200)
        await test_endpoint(client, "/agents/", viewer_token, viewer_id, 200)
        await test_endpoint(client, "/tools/", viewer_token, viewer_id, 200)

        # Test editor (should be able to view and create)
        print("\n   Testing EDITOR role:")
        await test_endpoint(client, "/workflows/", editor_token, editor_id, 200)
        await test_endpoint(client, "/agents/", editor_token, editor_id, 200)
        await test_endpoint(client, "/tools/", editor_token, editor_id, 200)

        # Test admin (should be able to do everything)
        print("\n   Testing ADMIN role:")
        await test_endpoint(client, "/workflows/", admin_token, admin_id, 200)
        await test_endpoint(client, "/agents/", admin_token, admin_id, 200)
        await test_endpoint(client, "/tools/", admin_token, admin_id, 200)

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
