# Migration Guide: Old RBAC SDK → New RBAC SDK

This guide helps you migrate from the old RBAC SDK (in `/rbac`) to the new production-ready RBAC SDK.

## Key Differences

| Feature | Old SDK | New SDK |
|---------|---------|---------|
| **Location** | `python_apps/rbac` | `python_packages/rbac-sdk` |
| **FastAPI Guards** | Manual implementation | Built-in `require_permission_async` |
| **Caching** | No caching | Built-in with 208x speedup |
| **API Key Validation** | Manual | Built-in HTTP and JWT validators |
| **Security** | Basic | Comprehensive (147 tests, fail-closed) |
| **Performance** | Unknown | 1M+ req/s, P99 < 1ms |
| **Documentation** | Minimal | Complete with examples |

## Migration Steps

### Step 1: Update Dependencies

**Old:**
```python
# In requirements.txt or pyproject.toml
# No explicit dependency, used python_apps/rbac directly
```

**New:**
```python
# In requirements.txt
-e python_packages/rbac-sdk

# Or in pyproject.toml
[tool.uv.sources]
rbac-sdk = { path = "../../python_packages/rbac-sdk", editable = true }
```

### Step 2: Update Imports

**Old:**
```python
from rbac_lib.validators.routes.config import route_validator_map
from rbac_lib.auth.impl import AccessTokenOrApikeyAuthentication
```

**New:**
```python
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
    api_key_http_validator,
    api_key_jwt_validator,
)
```

### Step 3: Replace Manual Guards

**Old Pattern:**
```python
from rbac_lib.validators.routes.config import route_validator_map

@router.get("/projects")
async def list_projects(
    validation_info: dict = Depends(
        route_validator_map[(APINamespace.RBAC_API, "list_projects")]
    ),
):
    # Manual permission check
    ...
```

**New Pattern:**
```python
from rbac_sdk import require_permission_async, resource_builders, principal_resolvers

guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

@router.get("/projects", dependencies=[Depends(guard)])
async def list_projects():
    # Permission automatically checked
    ...
```

### Step 4: Replace API Key Authentication

**Old Pattern:**
```python
from rbac_lib.auth.impl import ApikeyAuthentication

@router.get("/projects")
async def list_projects(
    api_key: Apikey = Depends(ApikeyAuthentication.authenticate),
):
    user_id = api_key.user_id
    ...
```

**New Pattern:**
```python
from rbac_sdk import api_key_http_validator, principal_resolvers

validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,
)

guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(
        validate_api_key=validator
    ),
)

@router.get("/projects", dependencies=[Depends(guard)])
async def list_projects():
    # API key automatically validated and permission checked
    ...
```

### Step 5: Replace Direct RBAC Checks

**Old Pattern:**
```python
from rbac_lib.validators.rbac_validator.rbac_validator_provider import RBACValidatorProvider

rbac_validator = RBACValidatorProvider.get_instance()
result = await rbac_validator.evaluate_rbac_permissions(
    request=request,
    logged_in_user=user,
    account_id=account_id,
    project_id=project_id,
    permissions_evaluation_request=request_data,
    db=db,
)
```

**New Pattern:**
```python
from rbac_sdk import check_access_async

allowed = await check_access_async(
    user_id=user.id,
    action="view_project",
    resource={
        "type": "project",
        "id": str(project_id),
        "organization_id": str(org_id),
        "account_id": str(account_id),
    }
)
```

### Step 6: Update Environment Variables

**Old:**
```bash
# Various environment variables
RBAC_SERVICE_URL=...
AUTH_SERVICE_URL=...
```

**New:**
```bash
# Standardized environment variables
export AUTH_API_BASE="http://localhost:8004"
export AUTHZ_SERVICE_URL="http://localhost:8181"
export API_KEY_SECRET="your-secret-key"
export API_KEY_ALGORITHM="HS256"
```

## Complete Migration Example

### Before (Old SDK)

```python
# python_apps/my_service/routers/projects.py
from fastapi import APIRouter, Depends
from rbac_lib.validators.routes.config import route_validator_map
from rbac_lib.auth.impl import ApikeyAuthentication
from elevaitelib.schemas import api as api_schemas

router = APIRouter()

@router.get("/projects")
async def list_projects(
    api_key: Apikey = Depends(ApikeyAuthentication.authenticate),
    validation_info: dict = Depends(
        route_validator_map[(api_schemas.APINamespace.MY_API, "list_projects")]
    ),
):
    # Manual permission logic
    user_id = api_key.user_id
    # ... fetch projects ...
    return {"projects": [...]}

@router.post("/projects")
async def create_project(
    api_key: Apikey = Depends(ApikeyAuthentication.authenticate),
    validation_info: dict = Depends(
        route_validator_map[(api_schemas.APINamespace.MY_API, "create_project")]
    ),
):
    # Manual permission logic
    user_id = api_key.user_id
    # ... create project ...
    return {"id": "..."}
```

### After (New SDK)

```python
# python_apps/my_service/routers/projects.py
from fastapi import APIRouter, Depends
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
)

router = APIRouter()

# Create reusable guards
guard_view = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

guard_edit = require_permission_async(
    action="edit_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

@router.get("/projects", dependencies=[Depends(guard_view)])
async def list_projects():
    # Permission automatically checked
    # ... fetch projects ...
    return {"projects": [...]}

@router.post("/projects", dependencies=[Depends(guard_edit)])
async def create_project():
    # Permission automatically checked
    # ... create project ...
    return {"id": "..."}
```

## Helper Function Pattern (Recommended)

For even cleaner code, create a helper function:

```python
# python_apps/my_service/util.py
from typing import Awaitable, Callable
from fastapi import Request
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
    HDR_PROJECT_ID,
    HDR_ACCOUNT_ID,
    HDR_ORG_ID,
)

def api_key_or_user_guard(action: str) -> Callable[[Request], Awaitable[None]]:
    """Create a guard for the given action with standard configuration."""
    return require_permission_async(
        action=action,
        resource_builder=resource_builders.project_from_headers(
            project_header=HDR_PROJECT_ID,
            account_header=HDR_ACCOUNT_ID,
            org_header=HDR_ORG_ID,
        ),
        principal_resolver=principal_resolvers.api_key_or_user(),
    )
```

Then use it in your routers:

```python
# python_apps/my_service/routers/projects.py
from ..util import api_key_or_user_guard

@router.get("/projects", dependencies=[Depends(api_key_or_user_guard("view_project"))])
async def list_projects():
    ...

@router.post("/projects", dependencies=[Depends(api_key_or_user_guard("edit_project"))])
async def create_project():
    ...
```

## Breaking Changes

### 1. User ID Type

**Old:** Integer user IDs
```python
user_id = 123  # Integer
```

**New:** String user IDs
```python
user_id = "user-123"  # String
```

### 2. Resource Structure

**Old:** Various structures
```python
resource = {
    "project_id": "...",
    "org_id": "...",
}
```

**New:** Standardized structure
```python
resource = {
    "type": "project",  # Required
    "id": "...",  # Required
    "organization_id": "...",  # Required
    "account_id": "...",  # Optional
}
```

### 3. Header Names

**Old:** Various header names
```python
X-User-ID
X-Org-ID
X-Project-ID
```

**New:** Standardized header names
```python
X-elevAIte-UserId
X-elevAIte-OrganizationId
X-elevAIte-ProjectId
X-elevAIte-AccountId
X-elevAIte-apikey
```

### 4. Error Responses

**Old:** Various error formats
```python
{"error": "Access denied"}
```

**New:** Standard FastAPI HTTPException
```python
{
    "detail": "Access denied: user does not have permission to perform edit_project on project"
}
```

## Testing Your Migration

### 1. Unit Tests

```python
from unittest.mock import Mock, patch
from rbac_sdk import require_permission_async, resource_builders, principal_resolvers

@pytest.mark.asyncio
@patch("rbac_sdk.fastapi_helpers.check_access_async")
async def test_guard_allows_access(mock_check_access):
    mock_check_access.return_value = True
    
    guard = require_permission_async(
        action="view_project",
        resource_builder=resource_builders.project_from_headers(),
        principal_resolver=principal_resolvers.api_key_or_user(),
    )
    
    request = Mock()
    request.headers = {
        "X-elevAIte-UserId": "user-123",
        "X-elevAIte-ProjectId": "proj-uuid",
        "X-elevAIte-OrganizationId": "org-uuid",
    }
    
    # Should not raise
    await guard(request)
```

### 2. Integration Tests

```python
from fastapi.testclient import TestClient

def test_list_projects_with_permission():
    client = TestClient(app)
    response = client.get(
        "/projects",
        headers={
            "X-elevAIte-UserId": "user-123",
            "X-elevAIte-ProjectId": "proj-uuid",
            "X-elevAIte-OrganizationId": "org-uuid",
        }
    )
    assert response.status_code == 200

def test_list_projects_without_permission():
    client = TestClient(app)
    response = client.get(
        "/projects",
        headers={
            "X-elevAIte-UserId": "unauthorized-user",
            "X-elevAIte-ProjectId": "proj-uuid",
            "X-elevAIte-OrganizationId": "org-uuid",
        }
    )
    assert response.status_code == 403
```

## Rollback Plan

If you need to rollback:

1. **Keep old code:** Don't delete old RBAC code until migration is complete
2. **Feature flag:** Use environment variable to switch between old and new
3. **Gradual migration:** Migrate one router at a time
4. **Monitor:** Watch for 401/403 errors after migration

## Getting Help

- **Examples:** See `python_apps/workflow-engine-poc` for complete working example
- **Tests:** See `python_packages/rbac-sdk/tests/` for usage patterns
- **Troubleshooting:** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **API Reference:** See [API_REFERENCE.md](./API_REFERENCE.md)

