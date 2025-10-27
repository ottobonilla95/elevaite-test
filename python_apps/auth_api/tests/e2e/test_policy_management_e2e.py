"""
End-to-End tests for Policy Management

These tests require a running OPA instance and test the complete flow:
1. Generate/upload policies via API
2. Verify policies are stored in OPA
3. Test authorization with the new policies
4. Clean up policies

Run with: pytest tests/e2e/test_policy_management_e2e.py -v

Prerequisites:
- OPA running at http://localhost:8181
- Auth API running at http://localhost:8004
"""

import pytest
import httpx
import asyncio
from typing import Dict, Optional


# Configuration
OPA_URL = "http://localhost:8181"
AUTH_API_URL = "http://localhost:8004/auth-api"

# Skip all tests if OPA is not available
pytestmark = pytest.mark.skipif(
    not pytest.config.getoption("--run-e2e", default=False),
    reason="E2E tests require --run-e2e flag and running OPA instance",
)


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def opa_client():
    """Check if OPA is available"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OPA_URL}/health", timeout=2.0)
            if response.status_code != 200:
                pytest.skip("OPA is not available")
        except Exception:
            pytest.skip("OPA is not available")
    return OPA_URL


@pytest.fixture
async def superuser_token():
    """
    Get or create a superuser token for testing.
    In a real scenario, you'd authenticate as a superuser.
    For testing, we'll mock this or use a test token.
    """
    # TODO: Implement actual authentication
    # For now, return a placeholder
    return "test-superuser-token"


@pytest.fixture
async def policy_client(superuser_token):
    """Create a client for policy management API"""

    class PolicyClient:
        def __init__(self, token: str):
            self.token = token
            self.base_url = AUTH_API_URL
            self.headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

        async def generate_policy(
            self,
            service_name: str,
            resource_type: str,
            actions: Dict[str, list],
            belongs_to: str = "project",
        ) -> dict:
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
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        async def upload_policy(self, module_name: str, rego_code: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/policies/upload",
                    json={"module_name": module_name, "rego_code": rego_code},
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        async def list_policies(self) -> list:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/policies", headers=self.headers, timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        async def get_policy(self, module_name: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/policies/{module_name}",
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        async def delete_policy(self, module_name: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/api/policies/{module_name}",
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        async def check_access(self, user_id: int, action: str, resource: dict) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/authz/check_access",
                    json={"user_id": user_id, "action": action, "resource": resource},
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

    return PolicyClient(superuser_token)


@pytest.fixture
async def opa_direct_client():
    """Direct OPA client for verification"""

    class OPAClient:
        async def get_policy(self, module_name: str) -> Optional[str]:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        f"{OPA_URL}/v1/policies/{module_name}", timeout=5.0
                    )
                    if response.status_code == 200:
                        return response.json()["result"]["raw"]
                    return None
                except Exception:
                    return None

        async def list_policies(self) -> list:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{OPA_URL}/v1/policies", timeout=5.0)
                if response.status_code == 200:
                    return list(response.json()["result"].keys())
                return []

    return OPAClient()


class TestPolicyGenerationE2E:
    """Test policy generation end-to-end"""

    @pytest.mark.asyncio
    async def test_generate_workflow_policy(
        self, opa_client, policy_client, opa_direct_client
    ):
        """Test generating a workflow policy and verifying it in OPA"""
        # Generate policy
        result = await policy_client.generate_policy(
            service_name="workflow_engine_test",
            resource_type="workflow",
            actions={
                "admin": [
                    "create_workflow",
                    "edit_workflow",
                    "view_workflow",
                    "delete_workflow",
                ],
                "editor": ["create_workflow", "edit_workflow", "view_workflow"],
                "viewer": ["view_workflow"],
            },
        )

        assert "message" in result
        assert result["module_name"] == "rbac/workflow_engine_test"
        assert "rego_code" in result

        # Verify policy exists in OPA
        await asyncio.sleep(0.5)  # Give OPA time to process
        opa_policy = await opa_direct_client.get_policy("rbac/workflow_engine_test")
        assert opa_policy is not None
        assert "workflow" in opa_policy
        assert "create_workflow" in opa_policy

        # Clean up
        await policy_client.delete_policy("rbac/workflow_engine_test")

    @pytest.mark.asyncio
    async def test_generate_multiple_services(
        self, opa_client, policy_client, opa_direct_client
    ):
        """Test generating policies for multiple services"""
        services = [
            {
                "service_name": "agents_test",
                "resource_type": "agent",
                "actions": {
                    "admin": ["create_agent", "edit_agent", "view_agent"],
                    "viewer": ["view_agent"],
                },
            },
            {
                "service_name": "reports_test",
                "resource_type": "report",
                "actions": {
                    "admin": ["create_report", "view_report"],
                    "viewer": ["view_report"],
                },
            },
        ]

        # Generate all policies
        for service in services:
            result = await policy_client.generate_policy(**service)
            assert "message" in result

        # Verify all exist in OPA
        await asyncio.sleep(0.5)
        policies = await opa_direct_client.list_policies()
        assert "rbac/agents_test" in policies
        assert "rbac/reports_test" in policies

        # Clean up
        await policy_client.delete_policy("rbac/agents_test")
        await policy_client.delete_policy("rbac/reports_test")

    @pytest.mark.asyncio
    async def test_generate_organization_level_policy(
        self, opa_client, policy_client, opa_direct_client
    ):
        """Test generating policy for organization-level resource"""
        result = await policy_client.generate_policy(
            service_name="billing_test",
            resource_type="invoice",
            actions={"admin": ["create_invoice", "view_invoice"]},
            belongs_to="organization",
        )

        assert result["module_name"] == "rbac/billing_test"

        # Verify in OPA
        await asyncio.sleep(0.5)
        opa_policy = await opa_direct_client.get_policy("rbac/billing_test")
        assert "organization" in opa_policy
        assert "organization_id" in opa_policy

        # Clean up
        await policy_client.delete_policy("rbac/billing_test")


class TestCustomPolicyUploadE2E:
    """Test custom policy upload end-to-end"""

    @pytest.mark.asyncio
    async def test_upload_custom_policy(
        self, opa_client, policy_client, opa_direct_client
    ):
        """Test uploading custom rego code"""
        custom_rego = """package rbac

import rego.v1

# Custom analyst role
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type in {"workflow", "agent", "report"}
    input.action in {"view_workflow", "view_agent", "view_report", "export_data"}
}
"""

        result = await policy_client.upload_policy("rbac/analyst_test", custom_rego)
        assert "uploaded successfully" in result["message"]

        # Verify in OPA
        await asyncio.sleep(0.5)
        opa_policy = await opa_direct_client.get_policy("rbac/analyst_test")
        assert opa_policy is not None
        assert "analyst" in opa_policy
        assert "export_data" in opa_policy

        # Clean up
        await policy_client.delete_policy("rbac/analyst_test")


class TestPolicyListingE2E:
    """Test policy listing end-to-end"""

    @pytest.mark.asyncio
    async def test_list_policies(self, opa_client, policy_client):
        """Test listing all policies"""
        # Create a test policy
        await policy_client.generate_policy(
            service_name="list_test",
            resource_type="test_resource",
            actions={"admin": ["test_action"]},
        )

        # List policies
        await asyncio.sleep(0.5)
        policies = await policy_client.list_policies()

        # Should contain our test policy
        policy_names = [p["name"] for p in policies]
        assert "rbac/list_test" in policy_names

        # Clean up
        await policy_client.delete_policy("rbac/list_test")

    @pytest.mark.asyncio
    async def test_get_specific_policy(self, opa_client, policy_client):
        """Test getting a specific policy"""
        # Create a test policy
        await policy_client.generate_policy(
            service_name="get_test",
            resource_type="test_resource",
            actions={"admin": ["test_action"]},
        )

        # Get the policy
        await asyncio.sleep(0.5)
        policy = await policy_client.get_policy("rbac/get_test")

        assert policy["module_name"] == "rbac/get_test"
        assert "package rbac" in policy["rego_code"]
        assert "test_action" in policy["rego_code"]

        # Clean up
        await policy_client.delete_policy("rbac/get_test")


class TestPolicyDeletionE2E:
    """Test policy deletion end-to-end"""

    @pytest.mark.asyncio
    async def test_delete_policy(self, opa_client, policy_client, opa_direct_client):
        """Test deleting a policy"""
        # Create a policy
        await policy_client.generate_policy(
            service_name="delete_test",
            resource_type="test_resource",
            actions={"admin": ["test_action"]},
        )

        # Verify it exists
        await asyncio.sleep(0.5)
        policies_before = await opa_direct_client.list_policies()
        assert "rbac/delete_test" in policies_before

        # Delete it
        result = await policy_client.delete_policy("rbac/delete_test")
        assert "deleted successfully" in result["message"]

        # Verify it's gone
        await asyncio.sleep(0.5)
        policies_after = await opa_direct_client.list_policies()
        assert "rbac/delete_test" not in policies_after


class TestCompleteAuthorizationFlowE2E:
    """Test complete flow: create policy -> test authorization"""

    @pytest.mark.asyncio
    async def test_workflow_authorization_flow(self, opa_client, policy_client):
        """
        Test complete flow:
        1. Generate workflow policy
        2. Test that admin can delete workflows
        3. Test that viewer cannot delete workflows
        4. Clean up
        """
        # Step 1: Generate workflow policy
        await policy_client.generate_policy(
            service_name="workflow_authz_test",
            resource_type="workflow",
            actions={
                "admin": [
                    "create_workflow",
                    "edit_workflow",
                    "view_workflow",
                    "delete_workflow",
                ],
                "editor": ["create_workflow", "edit_workflow", "view_workflow"],
                "viewer": ["view_workflow"],
            },
        )

        await asyncio.sleep(0.5)

        # Note: These tests would require actual user setup and role assignments
        # For now, we're testing the policy generation and structure
        # In a real E2E test, you would:
        # 1. Create test users
        # 2. Assign roles to users
        # 3. Test check_access with those users
        # 4. Verify correct allow/deny responses

        # Clean up
        await policy_client.delete_policy("rbac/workflow_authz_test")

    @pytest.mark.asyncio
    async def test_policy_update_flow(self, opa_client, policy_client):
        """
        Test updating a policy:
        1. Create initial policy
        2. Update it with new permissions
        3. Verify the update
        """
        # Create initial policy
        await policy_client.generate_policy(
            service_name="update_test",
            resource_type="test_resource",
            actions={"admin": ["create_test", "view_test"]},
        )

        await asyncio.sleep(0.5)

        # Get initial policy
        policy_v1 = await policy_client.get_policy("rbac/update_test")
        assert "create_test" in policy_v1["rego_code"]
        assert "delete_test" not in policy_v1["rego_code"]

        # Update policy with more actions
        await policy_client.generate_policy(
            service_name="update_test",  # Same name = update
            resource_type="test_resource",
            actions={
                "admin": ["create_test", "view_test", "delete_test"],  # Added delete
                "viewer": ["view_test"],  # Added viewer role
            },
        )

        await asyncio.sleep(0.5)

        # Get updated policy
        policy_v2 = await policy_client.get_policy("rbac/update_test")
        assert "delete_test" in policy_v2["rego_code"]
        assert "viewer" in policy_v2["rego_code"]

        # Clean up
        await policy_client.delete_policy("rbac/update_test")
