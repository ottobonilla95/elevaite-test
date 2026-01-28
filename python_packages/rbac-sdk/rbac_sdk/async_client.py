from __future__ import annotations
from typing import Any, Dict, Optional, Union
import os
import httpx

# Updated to point to Auth API's authz endpoint
DEFAULT_AUTHZ_SERVICE_URL = os.getenv("AUTHZ_SERVICE_URL", "http://localhost:8004")

# Tenant header name
HDR_TENANT_ID = "X-Tenant-ID"


async def check_access_async(
    *,
    user_id: Union[int, str],
    action: str,
    resource: Dict[str, Any],
    base_url: Optional[str] = None,
    timeout: float = 2.0,
    tenant_id: Optional[str] = None,
) -> bool:
    """
    Async variant of check_access that calls the unified Auth API authorization service.

    This now calls the Auth API's /api/authz/check_access endpoint which:
    1. Validates user exists and is ACTIVE
    2. Retrieves user's role assignments
    3. Calls OPA to evaluate the policy

    Args:
        user_id: User ID (int or string that can be converted to int).
        action: Action string (e.g., "view_project", "update_project").
        resource: Dict with keys: type, id, organization_id, account_id (optional).
        base_url: Override base URL (default uses AUTHZ_SERVICE_URL env).
        timeout: Request timeout seconds.
        tenant_id: Tenant ID to pass in X-Tenant-ID header (required for multi-tenant auth-api).

    Returns:
        True if allowed, False otherwise.
        Fails closed: network errors/timeouts return False.

    Environment Variables:
        RBAC_SDK_BYPASS_AUTHZ: If set to "true", "1", or "yes", always returns True (for E2E testing only).
    """
    # Bypass mode for E2E testing (NOT for production)
    if os.getenv("RBAC_SDK_BYPASS_AUTHZ", "").lower() in ("true", "1", "yes"):
        return True

    # Convert user_id to int - Auth API requires integer user IDs
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        # Fail closed - invalid user ID format
        return False

    url = (
        f"{(base_url or DEFAULT_AUTHZ_SERVICE_URL).rstrip('/')}/api/authz/check_access"
    )
    payload = {"user_id": user_id_int, "action": action, "resource": resource}

    # Build headers with tenant ID if provided
    headers: Dict[str, str] = {}
    if tenant_id:
        headers[HDR_TENANT_ID] = tenant_id

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url, json=payload, headers=headers if headers else None
            )
            if resp.status_code != 200:
                return False
            data = resp.json()
            return bool(data.get("allowed"))
    except Exception:
        return False
