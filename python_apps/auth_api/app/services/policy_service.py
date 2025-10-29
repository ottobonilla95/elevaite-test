"""
OPA Policy Management Service

Provides dynamic policy management via OPA's REST API.
Allows updating authorization policies without redeploying.
"""

import httpx
import logging
from typing import Dict, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class PolicyService:
    """Manage OPA policies dynamically via API"""

    def __init__(self):
        # Extract base URL from OPA_URL (remove the /v1/data/rbac/allow part)
        self.opa_base_url = settings.OPA_URL.rsplit("/v1/data", 1)[0]
        self.policy_base_url = f"{self.opa_base_url}/v1/policies"
        logger.info(f"PolicyService initialized with OPA at {self.opa_base_url}")

    async def upload_policy(self, module_name: str, rego_code: str) -> bool:
        """
        Upload or update a policy module in OPA.

        Args:
            module_name: Name of the policy module (e.g., "rbac/workflows")
            rego_code: The rego policy code as a string

        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.policy_base_url}/{module_name}",
                    content=rego_code,
                    headers={"Content-Type": "text/plain"},
                )

                if response.status_code == 200:
                    logger.info(f"Successfully uploaded policy: {module_name}")
                    return True
                else:
                    logger.error(f"Failed to upload policy {module_name}: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error uploading policy {module_name}: {str(e)}")
            return False

    async def get_policy(self, module_name: str) -> Optional[str]:
        """
        Get a policy module from OPA.

        Args:
            module_name: Name of the policy module

        Returns:
            The rego code as a string, or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.policy_base_url}/{module_name}")

                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {}).get("raw", "")
                elif response.status_code == 404:
                    logger.warning(f"Policy not found: {module_name}")
                    return None
                else:
                    logger.error(f"Error getting policy {module_name}: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error getting policy {module_name}: {str(e)}")
            return None

    async def delete_policy(self, module_name: str) -> bool:
        """
        Delete a policy module from OPA.

        Args:
            module_name: Name of the policy module

        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(f"{self.policy_base_url}/{module_name}")

                if response.status_code == 200:
                    logger.info(f"Successfully deleted policy: {module_name}")
                    return True
                else:
                    logger.error(f"Failed to delete policy {module_name}: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting policy {module_name}: {str(e)}")
            return False

    async def list_policies(self) -> List[Dict[str, str]]:
        """
        List all policy modules in OPA.

        Returns:
            List of policy module names
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.policy_base_url)

                if response.status_code == 200:
                    result = response.json().get("result", {})
                    # Convert to list of dicts with module name and ID
                    policies = [{"id": policy_id, "name": policy_id} for policy_id in result.keys()]
                    return policies
                else:
                    logger.error(f"Error listing policies: {response.status_code} - {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error listing policies: {str(e)}")
            return []

    async def validate_rego_syntax(self, rego_code: str) -> tuple[bool, Optional[str]]:
        """
        Validate rego syntax by attempting to compile it.

        Args:
            rego_code: The rego code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to upload to a test module
            test_module = "rbac/test_validation"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.policy_base_url}/{test_module}",
                    content=rego_code,
                    headers={"Content-Type": "text/plain"},
                )

                if response.status_code == 200:
                    # Clean up test module
                    await self.delete_policy(test_module)
                    return True, None
                else:
                    error_msg = response.json().get("errors", [{}])[0].get("message", "Unknown syntax error")
                    return False, error_msg

        except Exception as e:
            return False, str(e)

    async def generate_service_policy(
        self,
        service_name: str,
        resource_type: str,
        actions: Dict[str, List[str]],
        belongs_to: str = "project",
    ) -> str:
        """
        Generate rego policy for a service.

        Args:
            service_name: Name of the service (e.g., "workflow_engine")
            resource_type: Type of resource (e.g., "workflow")
            actions: Dict mapping role to list of allowed actions
            belongs_to: What the resource belongs to (default: "project")

        Returns:
            Generated rego code as a string
        """

        # Generate valid_resource_match rule
        # When resource_type == belongs_to (e.g., project belongs to project),
        # use input.resource.id instead of input.resource.project_id
        if resource_type == belongs_to:
            resource_id_field = "id"
        else:
            resource_id_field = f"{belongs_to}_id"

        resource_match = f"""
# {service_name.replace("_", " ").title()} - Resource matching
# Resources of type '{resource_type}' belong to {belongs_to}s
valid_resource_match(assignment) if {{
    assignment.resource_type == "{belongs_to}"
    input.resource.type == "{resource_type}"
    input.resource.{resource_id_field} == assignment.resource_id
}}
"""

        # Generate role_check rules for each role
        role_checks = []
        for role, allowed_actions in actions.items():
            if not allowed_actions:
                continue

            # Format actions as rego set
            if len(allowed_actions) == 1:
                actions_condition = f'input.action == "{allowed_actions[0]}"'
            else:
                actions_set = "{" + ", ".join([f'"{a}"' for a in allowed_actions]) + "}"
                actions_condition = f"input.action in {actions_set}"

            role_checks.append(
                f"""
# {role.title()} permissions for {resource_type}
role_check(assignment) if {{
    assignment.role == "{role}"
    input.resource.type == "{resource_type}"
    {actions_condition}
}}"""
            )

        # Combine into full policy
        policy = f"""package rbac

import rego.v1

# ============================================================================
# {service_name.upper().replace("_", " ")} Service Permissions
# Auto-generated policy module
# Resource type: {resource_type}
# Belongs to: {belongs_to}
# ============================================================================

{resource_match}
{"".join(role_checks)}
"""
        return policy


# Singleton instance
_policy_service: Optional[PolicyService] = None


def get_policy_service() -> PolicyService:
    """Get or create the PolicyService singleton"""
    global _policy_service
    if _policy_service is None:
        _policy_service = PolicyService()
    return _policy_service
