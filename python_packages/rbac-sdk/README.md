rbac-sdk

A lightweight RBAC SDK for FastAPI services that delegates authorization decisions to the unified Auth API authorization service.

**Updated:** This SDK now points to Auth API's `/api/authz/check_access` endpoint which provides:

- User status validation (ACTIVE users only)
- Role-based access control (RBAC)
- OPA-based policy evaluation

## Configuration

- Configure `AUTHZ_SERVICE_URL` (default: `http://localhost:8004/auth-api`)
- Use `from rbac_sdk.fastapi_helpers import require_permission, resource_builders`

## Usage

```python
from rbac_sdk import check_access

# Check if user has access
allowed = check_access(
    user_id=123,  # Integer user ID from Auth API
    action="view_project",
    resource={
        "type": "project",
        "id": "proj-uuid",
        "organization_id": "org-uuid",
        "account_id": "acct-uuid"
    }
)
```
