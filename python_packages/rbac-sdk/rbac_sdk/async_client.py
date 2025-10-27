from __future__ import annotations
from typing import Any, Dict, Optional
import os
import httpx

# Updated to point to Auth API's authz endpoint
DEFAULT_AUTHZ_SERVICE_URL = os.getenv("AUTHZ_SERVICE_URL", "http://localhost:8004")


async def check_access_async(
    *,
    user_id: int,
    action: str,
    resource: Dict[str, Any],
    base_url: Optional[str] = None,
    timeout: float = 2.0,
) -> bool:
    """
    Async variant of check_access that calls the unified Auth API authorization service.

    This now calls the Auth API's /api/authz/check_access endpoint which:
    1. Validates user exists and is ACTIVE
    2. Retrieves user's role assignments
    3. Calls OPA to evaluate the policy

    Args:
        user_id: Integer user ID from Auth API users table.
        action: Action string (e.g., "view_project", "update_project").
        resource: Dict with keys: type, id, organization_id, account_id (optional).
        base_url: Override base URL (default uses AUTHZ_SERVICE_URL env).
        timeout: Request timeout seconds.

    Returns:
        True if allowed, False otherwise.
        Fails closed: network errors/timeouts return False.
    """
    url = f"{(base_url or DEFAULT_AUTHZ_SERVICE_URL).rstrip('/')}/api/authz/check_access"
    payload = {"user_id": user_id, "action": action, "resource": resource}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                return False
            data = resp.json()
            return bool(data.get("allowed"))
    except Exception:
        return False
