import os
from typing import Any, Dict, Union
import requests

# Updated to point to Auth API's authz endpoint
DEFAULT_AUTHZ_SERVICE_URL = os.getenv("AUTHZ_SERVICE_URL", "http://localhost:8004")


class RBACClientError(Exception):
    """Exception raised when RBAC/AuthZ service call fails."""

    pass


def check_access(
    user_id: Union[int, str],
    action: str,
    resource: Dict[str, Any],
    *,
    base_url: str | None = None,
    timeout: float = 5.0,
) -> bool:
    """
    Synchronous client for the unified Auth API authorization service.

    This now calls the Auth API's /api/authz/check_access endpoint which:
    1. Validates user exists and is ACTIVE
    2. Retrieves user's role assignments
    3. Calls OPA to evaluate the policy

    Args:
        user_id: User ID (int or string that can be converted to int).
        action: Action string (e.g., "view_project", "update_project").
        resource: Dict with keys: type, id, organization_id, account_id (optional).
        base_url: Override base URL (default uses AUTHZ_SERVICE_URL env or http://localhost:8004).
        timeout: Request timeout seconds.

    Returns:
        True if allowed, False otherwise.

    Raises:
        RBACClientError: If the service call fails or user_id is invalid.
    """
    # Convert user_id to int - Auth API requires integer user IDs
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError) as e:
        raise RBACClientError(f"Invalid user_id format: {user_id}") from e

    url = (base_url or DEFAULT_AUTHZ_SERVICE_URL).rstrip("/") + "/api/authz/check_access"
    try:
        resp = requests.post(
            url,
            json={
                "user_id": user_id_int,
                "action": action,
                "resource": resource,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("allowed", False))
    except requests.RequestException as e:
        raise RBACClientError(f"AuthZ service call failed: {e}") from e
