# RBAC Integration for Workflow Engine PoC

## Overview

This document defines the RBAC (Role-Based Access Control) integration for the Workflow Engine PoC using the `rbac-sdk`.

## RBAC Actions

### Workflow Actions
- `view_project` - View workflows in a project (read-only)
- `edit_project` - Create, update, execute workflows in a project
- `manage_account` - Full control over workflows in an account (admin)

### Action Mapping

**Total: 55 protected endpoints across 9 routers**

#### Workflows (8 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /workflows/` | GET | `view_project` | project |
| `GET /workflows/{id}` | GET | `view_project` | project |
| `POST /workflows/` | POST | `edit_project` | project |
| `DELETE /workflows/{id}` | DELETE | `edit_project` | project |
| `POST /workflows/{id}/execute` | POST | `edit_project` | project |
| `GET /workflows/{id}/stream` | GET | `view_project` | project |
| `POST /workflows/{id}/stream` | POST | `edit_project` | project |
| `POST /workflows/validate` | POST | `view_project` | project |

#### Executions (4 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /executions/{id}` | GET | `view_project` | project |
| `GET /executions/{id}/results` | GET | `view_project` | project |
| `GET /executions/analytics` | GET | `view_project` | project |
| `GET /executions/{id}/stream` | GET | `view_project` | project |

#### Agents (8 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /agents/` | GET | `view_project` | project |
| `GET /agents/{id}` | GET | `view_project` | project |
| `POST /agents/` | POST | `edit_project` | project |
| `PUT /agents/{id}` | PUT | `edit_project` | project |
| `DELETE /agents/{id}` | DELETE | `edit_project` | project |
| `GET /agents/{id}/tools` | GET | `view_project` | project |
| `POST /agents/{id}/tools` | POST | `edit_project` | project |
| `PATCH /agents/{id}/tools/{tool_id}` | PATCH | `edit_project` | project |
| `DELETE /agents/{id}/tools/{tool_id}` | DELETE | `edit_project` | project |

#### Tools (20 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /tools/` | GET | `view_project` | project |
| `GET /tools/{tool_name}` | GET | `view_project` | project |
| `POST /tools/db` | POST | `edit_project` | project |
| `GET /tools/db` | GET | `view_project` | project |
| `GET /tools/db/{tool_id}` | GET | `view_project` | project |
| `PATCH /tools/db/{tool_id}` | PATCH | `edit_project` | project |
| `DELETE /tools/db/{tool_id}` | DELETE | `edit_project` | project |
| `POST /tools/categories` | POST | `edit_project` | project |
| `GET /tools/categories` | GET | `view_project` | project |
| `PATCH /tools/categories/{category_id}` | PATCH | `edit_project` | project |
| `GET /tools/categories/{category_id}` | GET | `view_project` | project |
| `DELETE /tools/categories/{category_id}` | DELETE | `edit_project` | project |
| `POST /tools/mcp-servers` | POST | `edit_project` | project |
| `GET /tools/mcp-servers` | GET | `view_project` | project |
| `GET /tools/mcp-servers/{server_id}` | GET | `view_project` | project |
| `PATCH /tools/mcp-servers/{server_id}` | PATCH | `edit_project` | project |
| `DELETE /tools/mcp-servers/{server_id}` | DELETE | `edit_project` | project |
| `POST /tools/sync` | POST | `edit_project` | project |
| `PATCH /tools/{tool_name}` | PATCH | `edit_project` | project |
| `DELETE /tools/{tool_name}` | DELETE | `edit_project` | project |

#### Prompts (5 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /prompts/` | GET | `view_project` | project |
| `GET /prompts/{prompt_id}` | GET | `view_project` | project |
| `POST /prompts/` | POST | `edit_project` | project |
| `PATCH /prompts/{prompt_id}` | PATCH | `edit_project` | project |
| `DELETE /prompts/{prompt_id}` | DELETE | `edit_project` | project |

#### Files (1 endpoint)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `POST /files/upload` | POST | `edit_project` | project |

#### Messages (2 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /executions/{execution_id}/steps/{step_id}/messages` | GET | `view_project` | project |
| `POST /executions/{execution_id}/steps/{step_id}/messages` | POST | `edit_project` | project |

#### Approvals (4 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `GET /approvals/` | GET | `view_project` | project |
| `GET /approvals/{approval_id}` | GET | `view_project` | project |
| `POST /approvals/{approval_id}/approve` | POST | `edit_project` | project |
| `POST /approvals/{approval_id}/deny` | POST | `edit_project` | project |

#### Steps (3 endpoints)
| Endpoint | HTTP Method | Action Required | Resource Type |
|----------|-------------|-----------------|---------------|
| `POST /steps/register` | POST | `edit_project` | project |
| `GET /steps/` | GET | `view_project` | project |
| `GET /steps/{step_type}` | GET | `view_project` | project |

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

## Permission Management

### How Admins Can Change Permissions

Admins can manage user permissions through the Auth API. The Auth API provides endpoints for:

1. **Creating Role Assignments** - Assign roles to users at different levels
2. **Updating Role Assignments** - Change user roles
3. **Deleting Role Assignments** - Remove user access
4. **Listing Role Assignments** - View current permissions

#### Auth API Endpoints for Permission Management

**Base URL**: `http://localhost:8004/api/rbac`

##### 1. Create Role Assignment

Assign a role to a user at organization, account, or project level:

```bash
POST /api/rbac/user_role_assignments
Content-Type: application/json
Authorization: Bearer <admin_access_token>

{
  "user_id": 123,                  # User ID (integer)
  "role": "editor",                # viewer, editor, admin, superadmin
  "resource_type": "project",      # organization, account, project
  "resource_id": "project-uuid"    # UUID of the resource
}
```

**Role Types**:
- `viewer` - Read-only access (project level)
- `editor` - Create/edit/delete access (project level)
- `admin` - Full account access (account level)
- `superadmin` - Full organization access (organization level)

**Resource Types**:
- `organization` - For superadmin roles
- `account` - For admin roles
- `project` - For editor and viewer roles

**Note**: If an assignment already exists for the user on that resource, it will be updated with the new role.

##### 2. List User's Role Assignments

View all roles assigned to a user:

```bash
GET /api/rbac/user_role_assignments?user_id=<user-id>
Authorization: Bearer <admin_access_token>
```

Optional query parameters:
- `user_id` - Filter by user ID (integer)
- `resource_id` - Filter by resource UUID
- `resource_type` - Filter by resource type (organization, account, project)
- `skip` - Pagination offset (default: 0)
- `limit` - Pagination limit (default: 100, max: 1000)

Response:
```json
{
  "assignments": [
    {
      "user_id": 123,
      "role": "editor",
      "resource_type": "project",
      "resource_id": "project-uuid",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

##### 3. Delete Role Assignment

Remove a user's access:

```bash
DELETE /api/rbac/user_role_assignments/{user_id}/{resource_id}
Authorization: Bearer <admin_access_token>
```

**Note**: To update a role, use the create endpoint (POST) - it will automatically update if an assignment already exists.

##### 4. Check Authorization

Verify if a user has permission for a specific action:

```bash
POST /api/authz/check_access
Content-Type: application/json

{
  "user_id": 123,
  "action": "edit_project",
  "resource": {
    "type": "project",
    "id": "project-uuid",
    "account_id": "account-uuid",
    "organization_id": "org-uuid"
  }
}
```

Response:
```json
{
  "allowed": true,
  "reason": "User has editor role on project"
}
```

**Security Note**: This endpoint checks:
1. User exists
2. User status is ACTIVE (inactive/suspended/pending users are denied)
3. User has appropriate role assignment
4. OPA policy evaluation passes

### Permission Hierarchy

The RBAC system uses a hierarchical permission model:

```
Organization (superadmin)
  └── Account (admin)
      └── Project (editor, viewer)
```

- **Superadmin** at organization level has full access to all accounts and projects
- **Admin** at account level has full access to all projects in that account
- **Editor** at project level can create/edit/delete resources in that project
- **Viewer** at project level can only read resources in that project

### Common Permission Management Scenarios

#### Scenario 1: Grant Editor Access to a User

```bash
# Create editor role assignment
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "project-uuid-456"
  }'
```

#### Scenario 2: Promote User from Viewer to Editor

```bash
# Simply create a new assignment with the same user_id and resource_id
# The API will automatically update the existing assignment
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "project-uuid-456"
  }'
```

#### Scenario 3: Grant Account-Level Admin Access

```bash
# Create admin role assignment at account level
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "admin",
    "resource_type": "account",
    "resource_id": "account-uuid-456"
  }'
```

#### Scenario 4: Revoke User Access

```bash
# Delete the role assignment
curl -X DELETE http://localhost:8004/api/rbac/user_role_assignments/123/project-uuid-456 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Scenario 5: List All Assignments for a User

```bash
# Get all role assignments for a user
curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?user_id=123" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### Scenario 6: Check if User Has Permission

```bash
# Verify user can edit a project
curl -X POST http://localhost:8004/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "action": "edit_project",
    "resource": {
      "type": "project",
      "id": "project-uuid-456",
      "account_id": "account-uuid-789",
      "organization_id": "org-uuid-123"
    }
  }'
```

### Testing Permissions

After changing permissions, test them using the workflow-engine-poc endpoints:

```bash
# Get API key for the user
curl -X POST http://localhost:8004/api/auth/api-keys \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API Key",
    "expires_in_days": 30
  }'

# Test with the API key
curl -X GET http://localhost:8006/workflows/ \
  -H "X-elevAIte-apikey: $API_KEY_JWT" \
  -H "X-elevAIte-ProjectId: project-456" \
  -H "X-elevAIte-AccountId: account-456" \
  -H "X-elevAIte-OrganizationId: org-123"
```

## Implementation Status

1. ✅ Define RBAC actions
2. ✅ Add guards to workflow endpoints (8 endpoints)
3. ✅ Add guards to execution endpoints (4 endpoints)
4. ✅ Add guards to agent endpoints (8 endpoints)
5. ✅ Add guards to tools endpoints (20 endpoints)
6. ✅ Add guards to prompts endpoints (5 endpoints)
7. ✅ Add guards to files endpoints (1 endpoint)
8. ✅ Add guards to messages endpoints (2 endpoints)
9. ✅ Add guards to approvals endpoints (4 endpoints)
10. ✅ Add guards to steps endpoints (3 endpoints)
11. ✅ Create integration tests (18 E2E tests, 100% passing)
12. ✅ Update API documentation

**Total: 55 endpoints protected with RBAC guards**

