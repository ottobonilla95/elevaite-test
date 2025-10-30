# RBAC SDK API Reference

Complete API documentation for the RBAC SDK.

## Table of Contents

- [Guards](#guards)
- [Resource Builders](#resource-builders)
- [Principal Resolvers](#principal-resolvers)
- [API Key Validators](#api-key-validators)
- [Direct Access Checks](#direct-access-checks)
- [Constants](#constants)

## Guards

### `require_permission_async`

Create an async FastAPI dependency that checks permissions.

```python
def require_permission_async(
    *,
    action: str,
    resource_builder: Callable[[Request], Dict[str, Any]],
    principal_resolver: Callable[[Request], str] = _default_principal_resolver,
    base_url: Optional[str] = None,
) -> Callable[[Request], Awaitable[None]]
```

**Parameters:**
- `action` (str): The action being performed (e.g., "view_project", "edit_workflow")
- `resource_builder` (Callable): Function that extracts resource info from the request
- `principal_resolver` (Callable, optional): Function that extracts user ID from the request
- `base_url` (str, optional): OPA service URL (defaults to `AUTHZ_SERVICE_URL` env var)

**Returns:**
- Callable that can be used with `Depends()` in FastAPI routes

**Raises:**
- `HTTPException(403)`: If access is denied
- `HTTPException(401)`: If principal cannot be resolved
- `HTTPException(400)`: If resource cannot be built

**Example:**
```python
guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

@router.get("/projects", dependencies=[Depends(guard)])
async def list_projects():
    ...
```

### `require_permission`

Synchronous version of `require_permission_async`.

```python
def require_permission(
    *,
    action: str,
    resource_builder: Callable[[Request], Dict[str, Any]],
    principal_resolver: Callable[[Request], str] = _default_principal_resolver,
    base_url: Optional[str] = None,
) -> Callable[[Request], None]
```

**Note:** Use `require_permission_async` for async routes (recommended).

## Resource Builders

Resource builders extract resource information from HTTP requests.

### `resource_builders.project_from_headers`

Extract project resource from headers.

```python
@staticmethod
def project_from_headers(
    project_header: str = HDR_PROJECT_ID,
    account_header: str = HDR_ACCOUNT_ID,
    org_header: str = HDR_ORG_ID,
) -> Callable[[Request], Dict[str, Any]]
```

**Parameters:**
- `project_header` (str): Header name for project ID (default: "X-elevAIte-ProjectId")
- `account_header` (str): Header name for account ID (default: "X-elevAIte-AccountId")
- `org_header` (str): Header name for organization ID (default: "X-elevAIte-OrganizationId")

**Returns:**
- Function that extracts resource dict from request

**Raises:**
- `HTTPException(400)`: If required headers are missing

**Example:**
```python
builder = resource_builders.project_from_headers()
# Returns: {"type": "project", "id": "...", "organization_id": "...", "account_id": "..."}
```

### `resource_builders.account_from_headers`

Extract account resource from headers.

```python
@staticmethod
def account_from_headers(
    account_header: str = HDR_ACCOUNT_ID,
    org_header: str = HDR_ORG_ID,
) -> Callable[[Request], Dict[str, Any]]
```

**Returns:**
- Function that extracts account resource dict

**Example:**
```python
builder = resource_builders.account_from_headers()
# Returns: {"type": "account", "id": "...", "organization_id": "..."}
```

### `resource_builders.organization_from_headers`

Extract organization resource from headers.

```python
@staticmethod
def organization_from_headers(
    org_header: str = HDR_ORG_ID,
) -> Callable[[Request], Dict[str, Any]]
```

**Returns:**
- Function that extracts organization resource dict

**Example:**
```python
builder = resource_builders.organization_from_headers()
# Returns: {"type": "organization", "id": "..."}
```

## Principal Resolvers

Principal resolvers extract user identity from HTTP requests.

### `principal_resolvers.user_id_header`

Extract user ID from a header.

```python
@staticmethod
def user_id_header(
    header_name: str = HDR_USER_ID
) -> Callable[[Request], str]
```

**Parameters:**
- `header_name` (str): Header name (default: "X-elevAIte-UserId")

**Returns:**
- Function that extracts user ID from request

**Raises:**
- `HTTPException(401)`: If header is missing

**Example:**
```python
resolver = principal_resolvers.user_id_header()
# Extracts from X-elevAIte-UserId header
```

### `principal_resolvers.api_key_or_user`

Try API key first, fall back to user ID header.

```python
@staticmethod
def api_key_or_user(
    validate_api_key: Optional[Callable[[str, Request], Optional[str]]] = None,
    *,
    allow_insecure_apikey_as_principal: bool = False,
) -> Callable[[Request], str]
```

**Parameters:**
- `validate_api_key` (Callable, optional): Function to validate API key and return user ID
- `allow_insecure_apikey_as_principal` (bool): If True, use API key as principal without validation (INSECURE)

**Returns:**
- Function that extracts user ID from API key or user ID header

**Raises:**
- `HTTPException(401)`: If neither API key nor user ID header is present

**Example:**
```python
# With API key validation
validator = api_key_http_validator(base_url="http://localhost:8004")
resolver = principal_resolvers.api_key_or_user(validate_api_key=validator)

# Without validation (for testing only)
resolver = principal_resolvers.api_key_or_user()
```

## API Key Validators

### `api_key_http_validator`

Validate API keys via HTTP call to Auth API.

```python
def api_key_http_validator(
    base_url: Optional[str] = None,
    *,
    path: str = "/api/auth/validate-apikey",
    header_name: str = HDR_API_KEY,
    timeout: float = 3.0,
    cache_ttl: float = 60.0,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Callable[[str, Request], Optional[str]]
```

**Parameters:**
- `base_url` (str, optional): Auth API base URL (defaults to `AUTH_API_BASE` env var)
- `path` (str): Validation endpoint path
- `header_name` (str): API key header name
- `timeout` (float): Request timeout in seconds
- `cache_ttl` (float): Cache TTL in seconds (0 to disable)
- `extra_headers` (dict, optional): Additional headers to send

**Returns:**
- Function that validates API key and returns user ID (or None if invalid)

**Example:**
```python
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,  # Cache for 60 seconds
)
```

### `api_key_jwt_validator`

Validate JWT API keys locally.

```python
def api_key_jwt_validator(
    algorithm: Optional[str] = None,
    secret: Optional[str] = None,
    public_key: Optional[str] = None,
    require_type: str = "api_key",
) -> Callable[[str, Request], Optional[str]]
```

**Parameters:**
- `algorithm` (str, optional): JWT algorithm (defaults to `API_KEY_ALGORITHM` env var)
- `secret` (str, optional): Secret key for HS* algorithms (defaults to `API_KEY_SECRET` env var)
- `public_key` (str, optional): Public key for RS*/ES* algorithms (defaults to `API_KEY_PUBLIC_KEY` env var)
- `require_type` (str): Required value for "type" claim

**Returns:**
- Function that validates JWT and returns user ID from "sub" claim (or None if invalid)

**Example:**
```python
validator = api_key_jwt_validator(
    algorithm="HS256",
    secret="your-secret-key",
)
```

## Direct Access Checks

### `check_access`

Synchronous access check (no FastAPI required).

```python
def check_access(
    user_id: str,
    action: str,
    resource: Dict[str, Any],
    base_url: Optional[str] = None,
) -> bool
```

**Parameters:**
- `user_id` (str): User ID
- `action` (str): Action being performed
- `resource` (dict): Resource being accessed
- `base_url` (str, optional): OPA service URL

**Returns:**
- `True` if access is allowed, `False` otherwise

**Example:**
```python
allowed = check_access(
    user_id="user-123",
    action="view_project",
    resource={
        "type": "project",
        "id": "proj-uuid",
        "organization_id": "org-uuid",
    }
)
```

### `check_access_async`

Asynchronous access check.

```python
async def check_access_async(
    user_id: str,
    action: str,
    resource: Dict[str, Any],
    base_url: Optional[str] = None,
) -> bool
```

**Example:**
```python
allowed = await check_access_async(
    user_id="user-123",
    action="view_project",
    resource={
        "type": "project",
        "id": "proj-uuid",
        "organization_id": "org-uuid",
    }
)
```

## Constants

### Header Names

```python
HDR_USER_ID = "X-elevAIte-UserId"
HDR_ORG_ID = "X-elevAIte-OrganizationId"
HDR_ACCOUNT_ID = "X-elevAIte-AccountId"
HDR_PROJECT_ID = "X-elevAIte-ProjectId"
HDR_API_KEY = "X-elevAIte-apikey"
```

### Environment Variables

- `AUTH_API_BASE`: Auth API base URL (required for HTTP API key validation)
- `AUTHZ_SERVICE_URL`: OPA service URL (default: "http://localhost:8181")
- `API_KEY_ALGORITHM`: JWT algorithm for API keys (default: "HS256")
- `API_KEY_SECRET`: Secret key for HS* JWT algorithms
- `API_KEY_PUBLIC_KEY`: Public key for RS*/ES* JWT algorithms
- `RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL`: Allow using API key as principal without validation (default: "false")

