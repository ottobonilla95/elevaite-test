"""
Example: Setting up user/project-specific access rules

This example shows how to:
1. Give specific users access to specific projects
2. Set different permission levels per project
3. Check authorization
"""

import httpx
import asyncio


# Configuration
AUTH_API_URL = "http://localhost:8004/auth-api"
SUPERUSER_TOKEN = "your-superuser-token-here"


async def setup_user_project_access():
    """
    Example: Set up access for multiple users on multiple projects
    
    Scenario:
    - Alice: Admin on project-123, Viewer on project-456
    - Bob: Editor on project-123, Editor on project-456
    - Charlie: Viewer on project-456 only
    """
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {SUPERUSER_TOKEN}",
            "Content-Type": "application/json",
        }
        
        # Alice's permissions
        print("Setting up Alice's permissions...")
        
        # Alice is admin on project-123
        response = await client.post(
            f"{AUTH_API_URL}/api/rbac/role-assignments",
            json={
                "user_id": 1,  # Alice's user ID
                "role": "admin",
                "resource_type": "project",
                "resource_id": "project-123",
            },
            headers=headers,
        )
        print(f"  Alice admin on project-123: {response.status_code}")
        
        # Alice is viewer on project-456
        response = await client.post(
            f"{AUTH_API_URL}/api/rbac/role-assignments",
            json={
                "user_id": 1,
                "role": "viewer",
                "resource_type": "project",
                "resource_id": "project-456",
            },
            headers=headers,
        )
        print(f"  Alice viewer on project-456: {response.status_code}")
        
        # Bob's permissions
        print("\nSetting up Bob's permissions...")
        
        # Bob is editor on both projects
        for project_id in ["project-123", "project-456"]:
            response = await client.post(
                f"{AUTH_API_URL}/api/rbac/role-assignments",
                json={
                    "user_id": 2,  # Bob's user ID
                    "role": "editor",
                    "resource_type": "project",
                    "resource_id": project_id,
                },
                headers=headers,
            )
            print(f"  Bob editor on {project_id}: {response.status_code}")
        
        # Charlie's permissions
        print("\nSetting up Charlie's permissions...")
        
        # Charlie is viewer on project-456 only
        response = await client.post(
            f"{AUTH_API_URL}/api/rbac/role-assignments",
            json={
                "user_id": 3,  # Charlie's user ID
                "role": "viewer",
                "resource_type": "project",
                "resource_id": "project-456",
            },
            headers=headers,
        )
        print(f"  Charlie viewer on project-456: {response.status_code}")


async def test_authorization():
    """
    Test authorization for different users and actions
    """
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {SUPERUSER_TOKEN}",
            "Content-Type": "application/json",
        }
        
        test_cases = [
            # Alice tests
            {
                "name": "Alice can edit project-123 (admin)",
                "user_id": 1,
                "action": "edit_project",
                "resource": {
                    "type": "project",
                    "id": "project-123",
                    "organization_id": "org-1",
                    "account_id": "acc-1",
                },
                "expected": True,
            },
            {
                "name": "Alice can only view project-456 (viewer)",
                "user_id": 1,
                "action": "view_project",
                "resource": {
                    "type": "project",
                    "id": "project-456",
                    "organization_id": "org-1",
                    "account_id": "acc-1",
                },
                "expected": True,
            },
            {
                "name": "Alice CANNOT edit project-456 (viewer)",
                "user_id": 1,
                "action": "edit_project",
                "resource": {
                    "type": "project",
                    "id": "project-456",
                    "organization_id": "org-1",
                    "account_id": "acc-1",
                },
                "expected": False,
            },
            # Bob tests
            {
                "name": "Bob can edit project-123 (editor)",
                "user_id": 2,
                "action": "edit_project",
                "resource": {
                    "type": "project",
                    "id": "project-123",
                    "organization_id": "org-1",
                    "account_id": "acc-1",
                },
                "expected": True,
            },
            {
                "name": "Bob can edit project-456 (editor)",
                "user_id": 2,
                "action": "edit_project",
                "resource": {
                    "type": "project",
                    "id": "project-456",
                    "organization_id": "org-1",
                    "account_id": "acc-1",
                },
                "expected": True,
            },
            # Charlie tests
            {
                "name": "Charlie can view project-456 (viewer)",
                "user_id": 3,
                "action": "view_project",
                "resource": {
                    "type": "project",
                    "id": "project-456",
                    "organization_id": "org-1",
                    "account_id": "acc-1",
                },
                "expected": True,
            },
            {
                "name": "Charlie CANNOT access project-123 (no assignment)",
                "user_id": 3,
                "action": "view_project",
                "resource": {
                    "type": "project",
                    "id": "project-123",
                    "organization_id": "org-1",
                    "account_id": "acc-1",
                },
                "expected": False,
            },
        ]
        
        print("\n" + "=" * 80)
        print("Testing Authorization")
        print("=" * 80)
        
        for test in test_cases:
            response = await client.post(
                f"{AUTH_API_URL}/api/authz/check_access",
                json={
                    "user_id": test["user_id"],
                    "action": test["action"],
                    "resource": test["resource"],
                },
                headers=headers,
            )
            
            result = response.json()
            allowed = result.get("allowed", False)
            
            status = "✅ PASS" if allowed == test["expected"] else "❌ FAIL"
            print(f"{status} - {test['name']}")
            if allowed != test["expected"]:
                print(f"  Expected: {test['expected']}, Got: {allowed}")
                print(f"  Response: {result}")


async def main():
    """Run the example"""
    print("=" * 80)
    print("User/Project-Specific Access Example")
    print("=" * 80)
    
    # Step 1: Set up permissions
    await setup_user_project_access()
    
    # Step 2: Test authorization
    await test_authorization()
    
    print("\n" + "=" * 80)
    print("Example complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

