"""OPA (Open Policy Agent) service for authorization policy evaluation."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class OPAService:
    """Service for interacting with Open Policy Agent for authorization decisions."""

    def __init__(self, opa_url: Optional[str] = None):
        """
        Initialize OPA service.

        Args:
            opa_url: URL of the OPA server. Defaults to OPA_URL env var or http://localhost:8181
        """
        self.opa_url = (opa_url or os.getenv("OPA_URL", "http://localhost:8181")).rstrip("/")
        self.policy_path = "/v1/data/rbac/allow"
        self.enabled = os.getenv("OPA_ENABLED", "true").lower() in ("true", "1", "yes")
        self.timeout = float(os.getenv("OPA_TIMEOUT", "5.0"))

        if not self.enabled:
            logger.warning("OPA is disabled. All authorization checks will be bypassed!")

    async def check_access(
        self,
        user_id: int,
        user_status: str,
        user_assignments: List[Dict[str, Any]],
        action: str,
        resource: Dict[str, Any],
        permission_overrides: Optional[Dict[str, Any]] = None,
        user_groups: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Check if a user has access to perform an action on a resource.

        Args:
            user_id: User ID (integer from Auth API users table)
            user_status: User status (active, inactive, suspended, pending)
            user_assignments: List of user role assignments
            action: Action to perform (e.g., "view_project", "edit_project")
            resource: Resource being accessed (type, id, organization_id, account_id)
            permission_overrides: Optional permission overrides (allow/deny lists)
            user_groups: Optional list of group memberships with permissions

        Returns:
            Dict with:
                - allowed (bool): Whether access is allowed
                - deny_reason (str, optional): Reason for denial if not allowed

        Raises:
            HTTPException: If OPA service is unavailable
        """
        if not self.enabled:
            logger.warning(f"OPA disabled - allowing access for user {user_id} to {action} on {resource.get('type')}")
            return {"allowed": True}

        # Build OPA input
        user_data = {
            "id": str(user_id),
            "status": user_status,
            "assignments": user_assignments,
        }

        # Add permission overrides if provided
        if permission_overrides:
            user_data["overrides"] = permission_overrides

        # Add group memberships if provided
        if user_groups:
            user_data["groups"] = user_groups

        opa_input = {
            "input": {
                "user": user_data,
                "action": action,
                "resource": resource,
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.opa_url}{self.policy_path}",
                    json=opa_input,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                result = response.json()

                allowed = result.get("result", False)

                # Get deny reason if available
                deny_reason = None
                if not allowed:
                    # Try to get deny_reason from OPA response
                    deny_reason_response = await client.post(
                        f"{self.opa_url}/v1/data/rbac/deny_reason",
                        json=opa_input,
                        timeout=self.timeout,
                    )
                    if deny_reason_response.status_code == 200:
                        deny_reason_result = deny_reason_response.json()
                        deny_reason = deny_reason_result.get("result")

                logger.info(
                    f"OPA decision for user {user_id} ({user_status}) - {action} on {resource.get('type')}: "
                    f"{'ALLOWED' if allowed else 'DENIED'}" + (f" - Reason: {deny_reason}" if deny_reason else "")
                )

                return {
                    "allowed": allowed,
                    "deny_reason": deny_reason,
                }

        except httpx.TimeoutException:
            logger.error(f"OPA service timeout after {self.timeout}s")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authorization service timeout",
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"OPA service returned error: {e.response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authorization service error",
            )
        except Exception as e:
            logger.error(f"Unexpected error calling OPA: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authorization service unavailable",
            )

    async def health_check(self) -> bool:
        """
        Check if OPA service is healthy.

        Returns:
            True if OPA is healthy, False otherwise
        """
        if not self.enabled:
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.opa_url}/health",
                    timeout=2.0,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OPA health check failed: {e}")
            return False


# Singleton instance
_opa_service: Optional[OPAService] = None


def get_opa_service() -> OPAService:
    """Get or create the OPA service singleton."""
    global _opa_service
    if _opa_service is None:
        _opa_service = OPAService()
    return _opa_service
