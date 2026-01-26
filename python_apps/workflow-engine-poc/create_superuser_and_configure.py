#!/usr/bin/env python3
"""
Create a superuser and configure OPA policies for granular actions.

This script:
1. Creates a superuser in the Auth API database
2. Gets an access token for the superuser
3. Configures OPA policies for all granular actions
"""

import asyncio
import asyncpg
import httpx
import sys
import os
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
DB_NAME = "auth"  # Auth database
AUTH_SCHEMA = "public"  # Tables are in public schema

AUTH_API_URL = "http://localhost:8004"
SECRET_KEY = "test-secret-key-for-integration-tests"

# Superuser credentials
SUPERUSER_EMAIL = "superadmin@elevaite.com"
SUPERUSER_PASSWORD = "Admin123!"  # Shorter password for bcrypt
SUPERUSER_NAME = "Super Administrator"


async def create_superuser_in_db():
    """Create a superuser directly in the database."""
    print("\n📝 Step 1: Creating superuser in database...")

    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    try:
        # Check if user already exists
        existing_user = await conn.fetchrow(
            f'SELECT id, email, is_superuser FROM "{AUTH_SCHEMA}".users WHERE email = $1',
            SUPERUSER_EMAIL,
        )

        if existing_user:
            print(
                f"   User {SUPERUSER_EMAIL} already exists (ID: {existing_user['id']})"
            )

            # Make sure they're a superuser
            if not existing_user["is_superuser"]:
                await conn.execute(
                    f'UPDATE "{AUTH_SCHEMA}".users SET is_superuser = true WHERE id = $1',
                    existing_user["id"],
                )
                print("   ✅ Updated user to be superuser")
            else:
                print("   ✅ User is already a superuser")

            return existing_user["id"]

        # Create new superuser
        hashed_password = get_password_hash(SUPERUSER_PASSWORD)
        now = datetime.now(timezone.utc)

        user_id = await conn.fetchval(
            f'''
            INSERT INTO "{AUTH_SCHEMA}".users (
                email, hashed_password, full_name, status, is_verified, 
                is_superuser, is_password_temporary, created_at, updated_at,
                failed_login_attempts, mfa_enabled
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            ''',
            SUPERUSER_EMAIL,
            hashed_password,
            SUPERUSER_NAME,
            "active",
            True,
            True,  # is_superuser
            False,
            now,
            now,
            0,
            False,
        )

        print(f"   ✅ Created superuser: {SUPERUSER_EMAIL} (ID: {user_id})")
        return user_id

    finally:
        await conn.close()


def create_access_token(user_id: int) -> str:
    """Create an access token for the superuser."""
    payload = {
        "sub": str(user_id),
        "email": SUPERUSER_EMAIL,
        "type": "access",
        "tenant_id": "default",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


async def configure_workflow_engine_policies(token: str):
    """Configure OPA policies for the Workflow Engine with granular actions."""

    print("\n📝 Step 2: Configuring granular action policies...")

    # Define granular actions for each role
    viewer_actions = [
        "view_workflow",
        "view_agent",
        "view_tool",
        "view_tool_category",
        "view_mcp_server",
        "view_prompt",
        "view_execution",
        "view_step",
        "view_approval",
        "view_message",
    ]

    editor_actions = viewer_actions + [
        "create_workflow",
        "edit_workflow",
        "execute_workflow",
        "create_agent",
        "edit_agent",
        "create_tool",
        "edit_tool",
        "create_tool_category",
        "edit_tool_category",
        "create_mcp_server",
        "edit_mcp_server",
        "sync_tools",
        "create_prompt",
        "edit_prompt",
        "register_step",
        "approve_request",
        "deny_request",
        "send_message",
        "upload_file",
    ]

    admin_actions = editor_actions + [
        "delete_workflow",
        "delete_agent",
        "delete_tool",
        "delete_tool_category",
        "delete_mcp_server",
        "delete_prompt",
    ]

    policy_data = {
        "service_name": "workflow_engine",
        "resource_type": "project",
        "belongs_to": "project",
        "actions": {
            "viewer": viewer_actions,
            "editor": editor_actions,
            "admin": admin_actions,
        },
    }

    print(f"\n   Service: {policy_data['service_name']}")
    print(f"   Resource Type: {policy_data['resource_type']}")
    print(f"   Viewer: {len(viewer_actions)} actions")
    print(f"   Editor: {len(editor_actions)} actions")
    print(f"   Admin: {len(admin_actions)} actions")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{AUTH_API_URL}/api/policies/generate",
                json=policy_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                result = response.json()
                print(f"\n   ✅ {result['message']}")
                print(f"   Module: {result.get('module_name', 'N/A')}")
                return True
            else:
                print(f"\n   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return False


async def test_policy():
    """Test that the policy is working."""
    print("\n📝 Step 3: Testing policy decision...")

    test_input = {
        "user": {
            "id": "test-user-001",
            "status": "active",
            "assignments": [
                {
                    "role": "viewer",
                    "resource_type": "project",
                    "resource_id": "test-project-789",
                }
            ],
        },
        "resource": {
            "type": "project",
            "id": "test-project-789",
            "project_id": "test-project-789",
            "account_id": "test-account-456",
            "organization_id": "test-org-123",
        },
        "action": "view_workflow",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8181/v1/data/rbac/allow",
                json={"input": test_input},
            )

            if response.status_code == 200:
                result = response.json()
                allowed = result.get("result", False)

                print("\n   Test: Viewer trying to view_workflow")
                print("   Expected: True")
                print(f"   Actual: {allowed}")

                if allowed:
                    print("   ✅ Policy is working correctly!")
                else:
                    print("   ❌ Policy decision is incorrect!")

                return allowed
            else:
                print(f"   ❌ Error: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def main():
    """Main function."""
    print("=" * 60)
    print("Workflow Engine - Policy Configuration")
    print("=" * 60)

    # Step 1: Create superuser
    user_id = await create_superuser_in_db()

    # Step 2: Create access token
    print(f"\n   Creating access token for user ID: {user_id}")
    token = create_access_token(user_id)
    print("   ✅ Token created")

    # Step 3: Configure policies
    success = await configure_workflow_engine_policies(token)

    if not success:
        print("\n❌ Failed to configure policies")
        return

    # Step 4: Test policy
    await test_policy()

    # Summary
    print("\n" + "=" * 60)
    print("Configuration Complete!")
    print("=" * 60)
    print(f"\n✅ Superuser created: {SUPERUSER_EMAIL}")
    print(f"   Password: {SUPERUSER_PASSWORD}")
    print("\n✅ Granular action policies configured in OPA")
    print("\nNext steps:")
    print("1. Run: python test_granular_actions.py")
    print("2. Test with different roles and actions")
    print("\nSee GRANULAR_ACTIONS.md for the complete list of actions.")


if __name__ == "__main__":
    asyncio.run(main())
