# RBAC SDK

A production-ready Python SDK for Role-Based Access Control (RBAC) with FastAPI integration, OPA policy evaluation, and comprehensive security features.

## Features

- 🔐 **FastAPI Guards** - Declarative permission checks with `@Depends(guard)`
- 🚀 **High Performance** - Built-in caching with 208x speedup, 1M+ req/s throughput
- 🛡️ **Security Hardened** - Fail-closed design, circuit breaker, comprehensive security testing
- 🔄 **Async & Sync** - Full support for both async and sync FastAPI endpoints
- 🎯 **Flexible Authentication** - API keys (HTTP/JWT), user IDs, custom resolvers
- 🏗️ **Resource Builders** - Pre-built and custom resource extractors
- 📊 **Production Ready** - 147 tests, 99.49% coverage, real-world scenario testing

## Installation

```bash
pip install -e python_packages/rbac-sdk
```

## Quick Start

### 1. Basic Setup

```python
from fastapi import FastAPI, Depends
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
)

app = FastAPI()

# Create a guard for viewing projects
guard_view = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

# Use the guard in your endpoint
@app.get("/projects", dependencies=[Depends(guard_view)])
async def list_projects():
    return {"projects": [...]}
```

### 2. Environment Configuration

```bash
# Required: Auth API base URL
export AUTH_API_BASE="http://localhost:8004"

# Optional: OPA service URL (defaults to http://localhost:8181)
export AUTHZ_SERVICE_URL="http://localhost:8181"

# Optional: API key validation (for JWT API keys)
export API_KEY_SECRET="your-secret-key"
export API_KEY_ALGORITHM="HS256"
```

### 3. Required Headers

All API requests must include these headers:

```
X-elevAIte-UserId: <user_id>           # User ID from Auth API
X-elevAIte-ProjectId: <project_id>     # Project UUID
X-elevAIte-AccountId: <account_id>     # Account UUID
X-elevAIte-OrganizationId: <org_id>    # Organization UUID
```

**OR** use API key authentication:

```
X-elevAIte-apikey: <api_key>           # API key (JWT or plain)
X-elevAIte-ProjectId: <project_id>     # Project UUID
X-elevAIte-AccountId: <account_id>     # Account UUID
X-elevAIte-OrganizationId: <org_id>    # Organization UUID
```

## Core Concepts

### Actions

Actions define what operation is being performed. Common actions:

- `view_project` - Read-only access
- `edit_project` - Create, update, delete, execute
- `manage_account` - Account-level management
- `view_agent`, `edit_agent` - Agent operations
- `view_workflow`, `edit_workflow` - Workflow operations
- `execute_workflow` - Workflow execution

### Resources

Resources define what is being accessed:

```python
{
    "type": "project",
    "id": "project-uuid",
    "organization_id": "org-uuid",
    "account_id": "account-uuid"  # Optional
}
```

### Principals

Principals define who is making the request (user ID or service account).

## Usage Patterns

### Pattern 1: Simple Guard (Most Common)

Used in **workflow-engine-poc** for all endpoints:

```python
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
)

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

# Use in routes
@router.get("/workflows", dependencies=[Depends(guard_view)])
async def list_workflows():
    ...

@router.post("/workflows", dependencies=[Depends(guard_edit)])
async def create_workflow():
    ...

@router.delete("/workflows/{id}", dependencies=[Depends(guard_edit)])
async def delete_workflow(id: str):
    ...
```

**Real Example:** See `python_apps/workflow-engine-poc/workflow_engine_poc/util.py`

### Pattern 2: Helper Function (Recommended for DRY)

Create a helper to generate guards with consistent configuration:

```python
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

# Use it
@router.get("/agents", dependencies=[Depends(api_key_or_user_guard("view_agent"))])
async def list_agents():
    ...
```

**Real Example:** See `python_apps/workflow-engine-poc/workflow_engine_poc/util.py`

### Pattern 3: Custom Principal Resolver

For custom authentication schemes:

```python
from rbac_sdk import principal_resolvers

# Use custom header for user ID
custom_resolver = principal_resolvers.user_id_header(header_name="X-Custom-User")

guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=custom_resolver,
)
```

### Pattern 4: API Key Validation with Caching

For high-performance API key validation:

```python
from rbac_sdk import api_key_http_validator, principal_resolvers

# Create validator with caching (60s TTL)
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,  # Cache for 60 seconds
)

# Use in principal resolver
guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(
        validate_api_key=validator
    ),
)
```

### Pattern 5: JWT API Key Validation

For JWT-based API keys:

```python
from rbac_sdk import api_key_jwt_validator, principal_resolvers

# Create JWT validator
validator = api_key_jwt_validator(
    algorithm="HS256",
    secret="your-secret-key",
)

# Use in principal resolver
guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(
        validate_api_key=validator
    ),
)
```

### Pattern 6: Direct Access Check (No FastAPI)

For non-FastAPI code or custom logic:

```python
from rbac_sdk import check_access, check_access_async

# Sync version
allowed = check_access(
    user_id="user-123",
    action="view_project",
    resource={
        "type": "project",
        "id": "project-uuid",
        "organization_id": "org-uuid",
        "account_id": "account-uuid",
    }
)

# Async version
allowed = await check_access_async(
    user_id="user-123",
    action="view_project",
    resource={
        "type": "project",
        "id": "project-uuid",
        "organization_id": "org-uuid",
        "account_id": "account-uuid",
    }
)
```

**Real Example:** See `python_apps/auth_api/app/routers/authz.py`

## Real-World Examples

### Example 1: Workflow Engine PoC

The workflow-engine-poc uses the RBAC SDK for all 50+ endpoints across 9 routers.

**File:** `python_apps/workflow-engine-poc/workflow_engine_poc/util.py`

```python
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
    HDR_PROJECT_ID,
    HDR_ACCOUNT_ID,
    HDR_ORG_ID,
)

def api_key_or_user_guard(action: str):
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

**Usage in routers:**

```python
# python_apps/workflow-engine-poc/workflow_engine_poc/routers/workflows.py
from ..util import api_key_or_user_guard

@router.get("/", dependencies=[Depends(api_key_or_user_guard("view_workflow"))])
async def list_workflows():
    ...

@router.post("/", dependencies=[Depends(api_key_or_user_guard("edit_workflow"))])
async def create_workflow():
    ...
```

### Example 2: Auth API

The Auth API uses the SDK for authorization checks and provides the backend services.

**File:** `python_apps/auth_api/app/routers/authz.py`

```python
from app.schemas.rbac import AccessCheckRequest, AccessCheckResponse
from app.services.opa_service import get_opa_service

@router.post("/check_access", response_model=AccessCheckResponse)
async def check_access(
    request: AccessCheckRequest,
    session: AsyncSession = Depends(get_tenant_async_db),
):
    # Validate user exists and is active
    user = await session.get(User, request.user_id)
    if not user or user.status != "active":
        return AccessCheckResponse(allowed=False, deny_reason="user_not_active")

    # Get role assignments
    result = await session.execute(
        select(UserRoleAssignment).where(UserRoleAssignment.user_id == user.id)
    )
    assignments = result.scalars().all()

    # Call OPA for policy evaluation
    opa_service = get_opa_service()
    opa_result = await opa_service.check_access(
        user_id=user.id,
        user_status=user.status,
        user_assignments=assignments,
        action=request.action,
        resource=request.resource.dict(),
    )

    return AccessCheckResponse(allowed=opa_result.allowed)
```

## Performance

- **Cache Speedup:** 208x faster than API calls
- **Cache Hit Rate:** 90% with mixed access patterns
- **Throughput:** 1M+ req/s from cache, 28K req/s async
- **Latency:** P99 < 1ms for cached requests

## Security

- **Fail-Closed:** All errors result in denied access
- **Circuit Breaker:** Prevents cascading failures
- **Comprehensive Testing:** 40 security tests covering JWT attacks, SSRF, injection, etc.
- **Input Validation:** Protection against SQL injection, XSS, null bytes, unicode attacks

## Testing

```bash
# Run all tests
cd python_packages/rbac-sdk
uv run pytest

# Run specific test suites
uv run pytest tests/integration/  # Integration tests
uv run pytest tests/security/     # Security tests
uv run pytest tests/performance/  # Performance tests
uv run pytest tests/scenarios/    # Real-world scenarios
```

## Documentation

- [API Reference](./docs/API_REFERENCE.md) - Complete API documentation
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Migration Guide](./docs/MIGRATION.md) - Migrating from old RBAC SDK
- [Performance Tuning](./docs/PERFORMANCE.md) - Optimization guide

## Architecture

The SDK delegates authorization decisions to the Auth API's `/api/authz/check_access` endpoint which provides:

- User status validation (ACTIVE users only)
- Role-based access control (RBAC)
- OPA-based policy evaluation

## License

Proprietary - ElevAIte Platform
```
