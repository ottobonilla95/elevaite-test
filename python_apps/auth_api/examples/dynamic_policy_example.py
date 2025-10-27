"""
Example: Using Dynamic Policy Management API

This script demonstrates how to programmatically manage OPA policies
via the Auth API's policy management endpoints.
"""

import asyncio
import httpx
from typing import Dict, List


class PolicyManager:
    """Client for managing OPA policies via Auth API"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def generate_service_policy(
        self,
        service_name: str,
        resource_type: str,
        actions: Dict[str, List[str]],
        belongs_to: str = "project",
    ) -> dict:
        """Generate and upload a policy for a service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/policies/generate",
                json={
                    "service_name": service_name,
                    "resource_type": resource_type,
                    "actions": actions,
                    "belongs_to": belongs_to,
                },
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def upload_custom_policy(self, module_name: str, rego_code: str) -> dict:
        """Upload custom rego code"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/policies/upload",
                json={"module_name": module_name, "rego_code": rego_code},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def list_policies(self) -> List[dict]:
        """List all policies"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/policies", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_policy(self, module_name: str) -> dict:
        """Get a specific policy"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/policies/{module_name}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def delete_policy(self, module_name: str) -> dict:
        """Delete a policy"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/policies/{module_name}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()


async def main():
    """Example usage"""

    # Configuration
    AUTH_API_URL = "http://localhost:8004/auth-api"
    SUPERUSER_TOKEN = "your-superuser-token-here"  # Replace with actual token

    # Create policy manager
    pm = PolicyManager(AUTH_API_URL, SUPERUSER_TOKEN)

    print("🧪 Dynamic Policy Management Examples")
    print("=" * 50)
    print()

    # Example 1: Add Workflow Service
    print("📝 Example 1: Add Workflow Service")
    print("-" * 50)
    result = await pm.generate_service_policy(
        service_name="workflow_engine",
        resource_type="workflow",
        actions={
            "superadmin": [
                "create_workflow",
                "edit_workflow",
                "view_workflow",
                "delete_workflow",
                "execute_workflow",
            ],
            "admin": [
                "create_workflow",
                "edit_workflow",
                "view_workflow",
                "delete_workflow",
                "execute_workflow",
            ],
            "editor": [
                "create_workflow",
                "edit_workflow",
                "view_workflow",
                "execute_workflow",
            ],
            "viewer": ["view_workflow"],
        },
        belongs_to="project",
    )
    print(f"✅ {result['message']}")
    print(f"   Module: {result['module_name']}")
    print()

    # Example 2: Add Agent Service
    print("📝 Example 2: Add Agent Service")
    print("-" * 50)
    result = await pm.generate_service_policy(
        service_name="agent_studio",
        resource_type="agent",
        actions={
            "admin": [
                "create_agent",
                "edit_agent",
                "view_agent",
                "delete_agent",
                "execute_agent",
            ],
            "editor": ["create_agent", "edit_agent", "view_agent", "execute_agent"],
            "viewer": ["view_agent"],
        },
    )
    print(f"✅ {result['message']}")
    print()

    # Example 3: Add Report Service with Custom Permissions
    print("📝 Example 3: Add Report Service")
    print("-" * 50)
    result = await pm.generate_service_policy(
        service_name="reports",
        resource_type="report",
        actions={
            "admin": [
                "create_report",
                "edit_report",
                "view_report",
                "delete_report",
                "export_report",
            ],
            "editor": ["create_report", "edit_report", "view_report", "export_report"],
            "viewer": ["view_report", "export_report"],  # Viewers can export!
        },
    )
    print(f"✅ {result['message']}")
    print()

    # Example 4: Upload Custom Policy for Analyst Role
    print("📝 Example 4: Upload Custom Policy (Analyst Role)")
    print("-" * 50)
    custom_rego = """package rbac

import rego.v1

# Analyst role - can view and export data from any resource
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type in {"workflow", "agent", "report"}
    input.action in {"view_workflow", "view_agent", "view_report", "export_data"}
}

# Analysts can also view analytics dashboards
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "dashboard"
    input.action == "view_dashboard"
}
"""
    result = await pm.upload_custom_policy("rbac/analyst_role", custom_rego)
    print(f"✅ {result['message']}")
    print()

    # Example 5: List All Policies
    print("📋 Example 5: List All Policies")
    print("-" * 50)
    policies = await pm.list_policies()
    print(f"Found {len(policies)} policies:")
    for policy in policies:
        print(f"  - {policy['name']}")
    print()

    # Example 6: Get Specific Policy
    print("🔍 Example 6: Get Workflow Policy")
    print("-" * 50)
    policy = await pm.get_policy("rbac/workflow_engine")
    print(f"Module: {policy['module_name']}")
    print("Rego code:")
    print(policy["rego_code"][:200] + "...")  # First 200 chars
    print()

    # Example 7: Organization-Level Resource
    print("📝 Example 7: Add Organization-Level Resource")
    print("-" * 50)
    result = await pm.generate_service_policy(
        service_name="billing",
        resource_type="invoice",
        actions={
            "superadmin": ["create_invoice", "view_invoice", "delete_invoice"],
            "admin": ["view_invoice"],
        },
        belongs_to="organization",  # Belongs to org, not project!
    )
    print(f"✅ {result['message']}")
    print()

    print("✅ All examples completed!")
    print()
    print("💡 Next Steps:")
    print("  1. Build an admin UI for policy management")
    print("  2. Add policy versioning and rollback")
    print("  3. Add policy testing/validation UI")
    print("  4. Store policy metadata in database")


if __name__ == "__main__":
    asyncio.run(main())

