from __future__ import annotations
from typing import Any, Callable, Dict, Optional, Awaitable
from fastapi import Request, HTTPException
import os
import time
import requests

from .client import check_access

# Default header names
HDR_USER_ID = "X-elevAIte-UserId"
HDR_ORG_ID = "X-elevAIte-OrganizationId"
HDR_ACCOUNT_ID = "X-elevAIte-AccountId"
HDR_PROJECT_ID = "X-elevAIte-ProjectId"
HDR_API_KEY = "X-elevAIte-apikey"
HDR_TENANT_ID = "X-Tenant-ID"


def _default_principal_resolver(request: Request) -> str:
    user_id = request.headers.get(HDR_USER_ID)
    if not user_id:
        # You can swap this for your access-token based auth later
        raise HTTPException(status_code=401, detail="Missing X-elevAIte-UserId header")
    return user_id


class principal_resolvers:
    @staticmethod
    def user_id_header(header_name: str = HDR_USER_ID) -> Callable[[Request], str]:
        def resolver(request: Request) -> str:
            user_id = request.headers.get(header_name)
            if not user_id:
                raise HTTPException(
                    status_code=401, detail=f"Missing {header_name} header"
                )
            return user_id

        return resolver

    @staticmethod
    def api_key_or_user(
        validate_api_key: Optional[Callable[[str, Request], Optional[str]]] = None,
        *,
        allow_insecure_apikey_as_principal: bool = bool(
            os.getenv("RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL", "false").lower()
            in {"1", "true", "yes"}
        ),
    ) -> Callable[[Request], str]:
        """
        Resolve principal from API key if present, otherwise from user header.
        - If validate_api_key is provided, it must return a user_id (service account) for the apikey or None.
        - If RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT is true, validates the API key locally as a JWT using env config.
        - If not provided and allow_insecure_apikey_as_principal is true, uses the raw API key as the principal id (NOT recommended for prod).
        - Otherwise raises 401 when an API key is provided but no validator is configured.
        """

        def resolver(request: Request) -> str:
            api_key = request.headers.get(HDR_API_KEY)
            if api_key:
                # 1) explicit validator provided by caller
                if validate_api_key:
                    user_id = validate_api_key(api_key, request)
                    if not user_id:
                        raise HTTPException(status_code=401, detail="Invalid API key")
                    return user_id
                # 2) optional local JWT validation via env flag
                enable_local = os.getenv(
                    "RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT", "false"
                ).lower() in {"1", "true", "yes"}
                if enable_local:
                    validator = api_key_jwt_validator()
                    user_id = validator(api_key, request)
                    if user_id:
                        return user_id
                    raise HTTPException(status_code=401, detail="Invalid API key")
                # 3) dev-only insecure fallback
                if allow_insecure_apikey_as_principal:
                    return api_key
                raise HTTPException(
                    status_code=401,
                    detail="API key provided but no validator configured",
                )
            # Fallback to user id header
            return _default_principal_resolver(request)

        return resolver


# Convenience: an HTTP-based API key validator that calls the Auth API
# to map an API key to a service-account user_id. Includes a small TTL cache.
# Response is expected to be JSON with a 'user_id' field.
# Example endpoint: POST {AUTH_API_BASE}/api/auth/validate-apikey


def api_key_http_validator(
    base_url: Optional[str] = None,
    *,
    path: str = "/api/auth/validate-apikey",
    header_name: str = HDR_API_KEY,
    timeout: float = 3.0,
    cache_ttl: float = 60.0,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Callable[[str, Request], Optional[str]]:
    auth_base = (base_url or os.getenv("AUTH_API_BASE", "")).rstrip("/")
    if not auth_base:
        raise RuntimeError(
            "AUTH_API_BASE must be set or base_url provided for api_key_http_validator"
        )

    cache: Dict[str, tuple[str, float]] = {}

    def validate(api_key: str, _request: Request) -> Optional[str]:
        _ = _request  # satisfy linters for the Request parameter

        now = time.time()
        if cache_ttl > 0:
            entry = cache.get(api_key)
            if entry and entry[1] > now:
                return entry[0]
        try:
            url = f"{auth_base}{path}"
            headers = {header_name: api_key}
            if extra_headers:
                headers.update(extra_headers)
            resp = requests.post(url, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                return None
            data = resp.json()
            user_id = data.get("user_id")
            if not user_id:
                return None
            if cache_ttl > 0:
                cache[api_key] = (user_id, now + cache_ttl)
            return user_id
        except Exception:
            return None

    return validate


def api_key_jwt_validator(
    algorithm: Optional[str] = None,
    *,
    secret: Optional[str] = None,
    public_key: Optional[str] = None,
    require_type: Optional[str] = "api_key",
) -> Callable[[str, Request], Optional[str]]:
    """
    Validate API keys locally as JWTs and return the mapped service-account user_id (token 'sub').

    Configuration precedence:
      - parameters
      - environment variables: API_KEY_ALGORITHM, API_KEY_SECRET, API_KEY_PUBLIC_KEY

    Returns a callable: (api_key, request) -> user_id | None
    """
    alg = (algorithm or os.getenv("API_KEY_ALGORITHM", "HS256")).strip()
    sec = secret or os.getenv("API_KEY_SECRET")
    pub = public_key or os.getenv("API_KEY_PUBLIC_KEY")

    def validate(api_key: str, _request: Request) -> Optional[str]:
        try:
            from jose import jwt  # type: ignore
        except Exception:
            # jose not installed
            return None
        try:
            if alg.startswith("HS"):
                key = sec
            elif alg.startswith("RS") or alg.startswith("ES"):
                key = pub
            else:
                return None
            if not key:
                return None
            payload = jwt.decode(api_key, key, algorithms=[alg])
            if require_type is not None and payload.get("type") != require_type:
                return None
            sub = payload.get("sub")
            if not sub:
                return None
            return sub
        except Exception:
            return None

    return validate


class resource_builders:
    @staticmethod
    def project_from_headers(
        project_header: str = HDR_PROJECT_ID,
        account_header: str = HDR_ACCOUNT_ID,
        org_header: str = HDR_ORG_ID,
    ) -> Callable[[Request], Dict[str, Any]]:
        def builder(request: Request) -> Dict[str, Any]:
            project_id = request.headers.get(project_header)
            org_id = request.headers.get(org_header)
            account_id = request.headers.get(account_header)
            if not project_id:
                raise HTTPException(
                    status_code=400, detail=f"Missing {project_header} header"
                )
            if not org_id:
                raise HTTPException(
                    status_code=400, detail=f"Missing {org_header} header"
                )
            # account_id optional for project-scoped checks in current rego; include if present
            res: Dict[str, Any] = {
                "type": "project",
                "id": project_id,
                "organization_id": org_id,
            }
            if account_id:
                res["account_id"] = account_id
            return res

        return builder

    @staticmethod
    def account_from_headers(
        account_header: str = HDR_ACCOUNT_ID,
        org_header: str = HDR_ORG_ID,
    ) -> Callable[[Request], Dict[str, Any]]:
        def builder(request: Request) -> Dict[str, Any]:
            account_id = request.headers.get(account_header)
            org_id = request.headers.get(org_header)
            if not account_id:
                raise HTTPException(
                    status_code=400, detail=f"Missing {account_header} header"
                )
            if not org_id:
                raise HTTPException(
                    status_code=400, detail=f"Missing {org_header} header"
                )
            # For compatibility with rego that expects account_id on resource
            return {
                "type": "account",
                "id": account_id,
                "organization_id": org_id,
                "account_id": account_id,
            }

        return builder

    @staticmethod
    def organization_from_headers(
        org_header: str = HDR_ORG_ID,
    ) -> Callable[[Request], Dict[str, Any]]:
        def builder(request: Request) -> Dict[str, Any]:
            org_id = request.headers.get(org_header)
            if not org_id:
                raise HTTPException(
                    status_code=400, detail=f"Missing {org_header} header"
                )
            return {
                "type": "organization",
                "id": org_id,
                "organization_id": org_id,
            }

        return builder


# Async guard variant using httpx-based client
try:
    from .async_client import check_access_async  # type: ignore
except Exception:  # pragma: no cover - optional in minimal envs
    check_access_async = None  # type: ignore


def require_permission_async(
    *,
    action: str,
    resource_builder: Callable[[Request], Dict[str, Any]],
    principal_resolver: Callable[[Request], str] = _default_principal_resolver,
    base_url: Optional[str] = None,
) -> Callable[[Request], Awaitable[None]]:
    """
    Async FastAPI dependency factory that denies the request if RBAC denies access.
    This awaits the RBAC service call before the route handler executes.
    """

    async def dependency(request: Request) -> None:
        if check_access_async is None:
            raise HTTPException(
                status_code=500, detail="Async RBAC client not available"
            )
        user_id = principal_resolver(request)
        resource = resource_builder(request)
        # Extract tenant ID from request headers to pass to auth-api
        tenant_id = request.headers.get(HDR_TENANT_ID)
        allowed = await check_access_async(
            user_id=user_id,
            action=action,
            resource=resource,
            base_url=base_url,
            tenant_id=tenant_id,
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")

    return dependency


def require_permission(
    *,
    action: str,
    resource_builder: Callable[[Request], Dict[str, Any]],
    principal_resolver: Callable[[Request], str] = _default_principal_resolver,
    base_url: Optional[str] = None,
) -> Callable[[Request], None]:
    """
    FastAPI dependency factory that denies the request if the RBAC service denies access.

    Usage:
        guard = require_permission(action="view_project", resource_builder=resource_builders.project_from_headers())
        @router.get("/projects", dependencies=[Depends(guard)])
        def list_projects(...): ...
    """

    def dependency(request: Request) -> None:
        user_id = principal_resolver(request)
        resource = resource_builder(request)
        # Extract tenant ID from request headers to pass to auth-api
        tenant_id = request.headers.get(HDR_TENANT_ID)
        allowed = check_access(
            user_id=user_id,
            action=action,
            resource=resource,
            base_url=base_url,
            tenant_id=tenant_id,
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")

    return dependency
