import os
from typing import Awaitable, Callable

from fastapi import Request
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
    HDR_API_KEY,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)


# Allow bypassing RBAC for E2E testing (set SKIP_RBAC=true)
_SKIP_RBAC = os.getenv("SKIP_RBAC", "false").lower() in {"1", "true", "yes"}


async def _noop_guard(request: Request) -> None:
    """No-op guard that allows all requests (for testing)."""
    pass


def api_key_or_user_guard(action: str) -> Callable[[Request], Awaitable[None]]:
    if _SKIP_RBAC:
        return _noop_guard
    return require_permission_async(
        action=action,
        resource_builder=resource_builders.project_from_headers(
            project_header=HDR_PROJECT_ID,
            account_header=HDR_ACCOUNT_ID,
            org_header=HDR_ORG_ID,
        ),
        principal_resolver=principal_resolvers.api_key_or_user(),
    )


def user_guard(action: str) -> Callable[[Request], Awaitable[None]]:
    if _SKIP_RBAC:
        return _noop_guard
    return require_permission_async(
        action=action,
        resource_builder=resource_builders.project_from_headers(
            project_header=HDR_PROJECT_ID,
            account_header=HDR_ACCOUNT_ID,
            org_header=HDR_ORG_ID,
        ),
        principal_resolver=principal_resolvers.user_id_header(),
    )
