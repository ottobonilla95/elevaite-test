# RBAC Integration for Workflow Engine PoC

## Overview

This document defines the RBAC (Role-Based Access Control) integration for the Workflow Engine PoC using the `rbac-sdk`.

## RBAC Actions

### Workflow Actions
- `view_project` - View workflows in a project (read-only)
- `edit_project` - Create, update, execute workflows in a project
- `manage_account` - Full control over workflows in an account (admin)

### Action Mapping

| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /api/workflows/` | GET | `view_project` | project |
| `GET /api/workflows/{id}` | GET | `view_project` | project |
| `POST /api/workflows/` | POST | `edit_project` | project |
| `DELETE /api/workflows/{id}` | DELETE | `edit_project` | project |
| `POST /api/workflows/{id}/execute` | POST | `edit_project` | project |
| `GET /api/workflows/{id}/stream` | GET | `view_project` | project |
| `POST /api/workflows/validate` | POST | `view_project` | project |
| `GET /api/executions/` | GET | `view_project` | project |
| `GET /api/executions/{id}` | GET | `view_project` | project |
| `GET /api/executions/{id}/results` | GET | `view_project` | project |
| `GET /api/executions/{id}/stream` | GET | `view_project` | project |
| `GET /api/agents/` | GET | `view_project` | project |
| `GET /api/agents/{id}` | GET | `view_project` | project |
| `POST /api/agents/` | POST | `edit_project` | project |
| `PUT /api/agents/{id}` | PUT | `edit_project` | project |
| `DELETE /api/agents/{id}` | DELETE | `edit_project` | project |
| `GET /api/tools/` | GET | `view_project` | project |
| `POST /api/tools/` | POST | `edit_project` | project |
| `GET /api/prompts/` | GET | `view_project` | project |
| `POST /api/prompts/` | POST | `edit_project` | project |
| `GET /api/files/` | GET | `view_project` | project |
| `POST /api/files/upload` | POST | `edit_project` | project |
| `GET /api/messages/` | GET | `view_project` | project |
| `POST /api/messages/` | POST | `edit_project` | project |
| `GET /api/approvals/` | GET | `view_project` | project |
| `POST /api/approvals/{id}/approve` | POST | `edit_project` | project |
| `POST /api/approvals/{id}/deny` | POST | `edit_project` | project |

## Role Permissions

### Viewer
- Can view workflows, executions, agents, tools, prompts, files, messages, approvals
- **Cannot** create, update, delete, or execute anything

### Editor
- All viewer permissions
- Can create, update, delete workflows, agents, tools, prompts
- Can execute workflows
- Can upload files
- Can send messages
- Can approve/deny approval requests

### Admin (Account Level)
- All editor permissions for all projects in the account
- Can manage account-level resources

### Superadmin (Organization Level)
- Full access to all resources in the organization

## Required Headers

All API requests must include the following headers for RBAC:

```
X-elevAIte-UserId: <user_id>           # User ID from Auth API
X-elevAIte-ProjectId: <project_id>     # Project UUID
X-elevAIte-AccountId: <account_id>     # Account UUID
X-elevAIte-OrganizationId: <org_id>    # Organization UUID
```

**OR** use API key authentication:

```
X-elevAIte-apikey: <api_key_jwt>       # JWT API key with type="api_key"
X-elevAIte-ProjectId: <project_id>     # Project UUID
X-elevAIte-AccountId: <account_id>     # Account UUID
X-elevAIte-OrganizationId: <org_id>    # Organization UUID
```

## Implementation

### Guards

The SDK provides pre-built guards:

```python
from rbac_sdk import (
    require_permission_async,
    resource_builders,
    principal_resolvers,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)

# View guard (read-only)
_guard_view_project = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

# Edit guard (create/update/delete/execute)
_guard_edit_project = require_permission_async(
    action="edit_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)
```

### Usage in Routes

```python
@router.get("/workflows/", dependencies=[Depends(_guard_view_project)])
async def list_workflows(...):
    ...

@router.post("/workflows/", dependencies=[Depends(_guard_edit_project)])
async def create_workflow(...):
    ...
```

## Testing

### Manual Testing with curl

```bash
# Get access token from Auth API
TOKEN="<your_jwt_token>"

# List workflows (requires view_project permission)
curl -X GET http://localhost:8000/api/workflows/ \
  -H "X-elevAIte-UserId: 123" \
  -H "X-elevAIte-ProjectId: <project_uuid>" \
  -H "X-elevAIte-AccountId: <account_uuid>" \
  -H "X-elevAIte-OrganizationId: <org_uuid>"

# Create workflow (requires edit_project permission)
curl -X POST http://localhost:8000/api/workflows/ \
  -H "X-elevAIte-UserId: 123" \
  -H "X-elevAIte-ProjectId: <project_uuid>" \
  -H "X-elevAIte-AccountId: <account_uuid>" \
  -H "X-elevAIte-OrganizationId: <org_uuid>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Workflow", ...}'
```

### Integration Tests

See `tests/integration/test_rbac_integration.py` for comprehensive integration tests.

## Error Responses

### 401 Unauthorized
Missing or invalid user ID / API key

```json
{
  "detail": "Unauthorized"
}
```

### 403 Forbidden
User does not have required permission

```json
{
  "detail": "Forbidden"
}
```

### 400 Bad Request
Missing required headers (project_id, account_id, organization_id)

```json
{
  "detail": "Missing required header: X-elevAIte-ProjectId"
}
```

## Configuration

### Environment Variables

```bash
# Auth API URL for RBAC checks
AUTHZ_SERVICE_URL=http://localhost:8004

# OPA URL (optional, used by Auth API)
OPA_URL=http://localhost:8181
```

## Migration Guide

### Before (No RBAC)

```python
@router.get("/workflows/")
async def list_workflows(...):
    return WorkflowsService.list_workflows(...)
```

### After (With RBAC)

```python
@router.get("/workflows/", dependencies=[Depends(_guard_view_project)])
async def list_workflows(
    ...,
    # Add headers for Swagger UI testing
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    return WorkflowsService.list_workflows(...)
```

## Next Steps

1. ✅ Define RBAC actions
2. [ ] Add guards to workflow endpoints
3. [ ] Add guards to execution endpoints
4. [ ] Add guards to agent endpoints
5. [ ] Add guards to other resource endpoints
6. [ ] Create integration tests
7. [ ] Update API documentation

