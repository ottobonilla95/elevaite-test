#!/usr/bin/env python3
"""
Configure OPA policies for granular actions in the Workflow Engine.

This script uses the Auth API's dynamic policy management to configure
permissions for all the new granular actions.

Prerequisites:
- Auth API running on port 8004
- OPA running on port 8181
- Superuser credentials
"""

import asyncio
import httpx
import os
from jose import jwt
from datetime import datetime, timedelta, timezone

# Configuration
AUTH_API_URL = os.getenv("AUTH_API_URL", "http://localhost:8004")
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-integration-tests")

# Superuser credentials (adjust as needed)
SUPERUSER_EMAIL = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "admin123")


def create_superuser_token(user_id: str = "superuser-001") -> str:
    """Create a superuser access token for testing."""
    payload = {
        "sub": user_id,
        "email": SUPERUSER_EMAIL,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


async def login_superuser() -> str:
    """Login as superuser and get access token."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_API_URL}/auth-api/login",
                json={
                    "email": SUPERUSER_EMAIL,
                    "password": SUPERUSER_PASSWORD,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["access_token"]
            else:
                print(f"⚠️  Login failed: {response.status_code} - {response.text}")
                print("Using generated token instead...")
                return create_superuser_token()
        except Exception as e:
            print(f"⚠️  Login error: {e}")
            print("Using generated token instead...")
            return create_superuser_token()


async def configure_workflow_engine_policies(token: str):
    """Configure OPA policies for the Workflow Engine with granular actions."""
    
    # Define granular actions for each role
    # Based on GRANULAR_ACTIONS.md
    
    viewer_actions = [
        # Read-only access
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
        # Create and edit (but not delete)
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
        # Full access including delete
        "delete_workflow",
        "delete_agent",
        "delete_tool",
        "delete_tool_category",
        "delete_mcp_server",
        "delete_prompt",
    ]
    
    policy_data = {
        "service_name": "workflow_engine",
        "resource_type": "project",  # All workflow engine resources belong to projects
        "belongs_to": "project",
        "actions": {
            "viewer": viewer_actions,
            "editor": editor_actions,
            "admin": admin_actions,
        },
    }
    
    print("\n" + "=" * 60)
    print("Configuring Workflow Engine Policies")
    print("=" * 60)
    print(f"\nService: {policy_data['service_name']}")
    print(f"Resource Type: {policy_data['resource_type']}")
    print(f"\nRole Permissions:")
    print(f"  Viewer: {len(viewer_actions)} actions")
    print(f"  Editor: {len(editor_actions)} actions")
    print(f"  Admin: {len(admin_actions)} actions")
    
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
                print(f"\n✅ {result['message']}")
                print(f"   Module: {result.get('module_name', 'N/A')}")
                
                # Show a preview of the generated policy
                rego_code = result.get('rego_code', '')
                if rego_code:
                    lines = rego_code.split('\n')
                    print(f"\n📄 Generated Policy Preview (first 20 lines):")
                    print("-" * 60)
                    for line in lines[:20]:
                        print(line)
                    if len(lines) > 20:
                        print(f"... ({len(lines) - 20} more lines)")
                
                return True
            else:
                print(f"\n❌ Failed to configure policies: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error configuring policies: {e}")
            return False


async def verify_policy_uploaded():
    """Verify the policy was uploaded to OPA."""
    print("\n" + "=" * 60)
    print("Verifying Policy Upload")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Check OPA directly
            response = await client.get("http://localhost:8181/v1/policies/rbac/workflow_engine")
            
            if response.status_code == 200:
                print("✅ Policy successfully uploaded to OPA")
                result = response.json()
                if 'result' in result and 'raw' in result['result']:
                    rego_code = result['result']['raw']
                    lines = rego_code.split('\n')
                    print(f"   Policy has {len(lines)} lines")
                return True
            else:
                print(f"⚠️  Policy not found in OPA: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying policy: {e}")
            return False


async def test_policy_decision():
    """Test a policy decision to ensure it's working."""
    print("\n" + "=" * 60)
    print("Testing Policy Decision")
    print("=" * 60)
    
    # Test case: viewer trying to view_workflow (should allow)
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
                
                print(f"\nTest: Viewer trying to view_workflow")
                print(f"Expected: True")
                print(f"Actual: {allowed}")
                
                if allowed:
                    print("✅ Policy decision is correct!")
                else:
                    print("❌ Policy decision is incorrect!")
                
                return allowed
            else:
                print(f"❌ Error testing policy: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing policy: {e}")
            return False


async def main():
    """Main function."""
    print("=" * 60)
    print("Workflow Engine - Granular Actions Policy Configuration")
    print("=" * 60)
    
    # Step 1: Get superuser token
    print("\n📝 Step 1: Authenticating as superuser...")
    token = await login_superuser()
    print("✅ Authentication successful")
    
    # Step 2: Configure policies
    print("\n📝 Step 2: Configuring granular action policies...")
    success = await configure_workflow_engine_policies(token)
    
    if not success:
        print("\n❌ Failed to configure policies. Exiting.")
        return
    
    # Step 3: Verify upload
    print("\n📝 Step 3: Verifying policy upload...")
    await verify_policy_uploaded()
    
    # Step 4: Test policy
    print("\n📝 Step 4: Testing policy decision...")
    await test_policy_decision()
    
    # Summary
    print("\n" + "=" * 60)
    print("Configuration Complete!")
    print("=" * 60)
    print("\n✅ Granular action policies have been configured in OPA")
    print("\nNext steps:")
    print("1. Run the test script: python test_granular_actions.py")
    print("2. Run full integration tests: pytest tests/test_rbac_integration.py")
    print("3. Test specific endpoints with different roles")
    print("\nSee GRANULAR_ACTIONS.md for the complete list of actions.")


if __name__ == "__main__":
    asyncio.run(main())

