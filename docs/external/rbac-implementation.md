# RBAC Implementation

Role-Based Access Control (RBAC) with OPA policy evaluation and fine-grained permission overrides.

## Overview

The RBAC system provides:
- **Hierarchical resource model**: Organization → Account → Project
- **Role-based permissions**: superadmin, admin, editor, viewer
- **OPA policy evaluation**: Centralized authorization decisions
- **Permission overrides**: Fine-grained allow/deny beyond roles
- **SDK for integration**: FastAPI guards and helpers

---

## Resource Hierarchy

```
Organization (top-level tenant)
    └── Account (business unit)
            └── Project (workspace)
```

| Resource | Description | Parent |
|----------|-------------|--------|
| Organization | Top-level tenant boundary | None |
| Account | Business unit within an org | Organization |
| Project | Individual workspace | Account |

---

## Roles

| Role | Scope | Permissions |
|------|-------|-------------|
| `superadmin` | Organization | Full access to everything in the organization |
| `admin` | Account | Full access to account and all its projects |
| `editor` | Project | Can edit and view project resources |
| `viewer` | Project | Can only view project resources |

### Role Inheritance

- **superadmin** on Organization → full access to all Accounts and Projects within
- **admin** on Account → full access to all Projects within that Account
- **editor/viewer** → project-level only, no inheritance

---

## Permission Actions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view_project` | View project resources | superadmin, admin, editor, viewer |
| `edit_project` | Modify project resources | superadmin, admin, editor |
| `manage_account` | Manage account settings | superadmin, admin |
| *(custom actions)* | Application-defined actions | Configured via overrides |

---

## Permission Overrides

Fine-grained control beyond role-based permissions:

| Field | Type | Description |
|-------|------|-------------|
| `allow_actions` | `string[]` | Actions explicitly allowed |
| `deny_actions` | `string[]` | Actions explicitly denied (**takes precedence**) |

**Evaluation Order:**
1. Check explicit `deny_actions` → if match, **DENY**
2. Check explicit `allow_actions` → if match, **ALLOW**
3. Fall back to role-based permissions

---

## Database Schema

### Core Tables

```sql
-- organizations: Top-level tenants
organizations (
    id          UUID PRIMARY KEY,
    name        VARCHAR UNIQUE,
    description VARCHAR,
    created_at  TIMESTAMP,
    updated_at  TIMESTAMP
)

-- accounts: Business units within organizations
accounts (
    id              UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    name            VARCHAR,
    description     VARCHAR,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
)

-- projects: Workspaces within accounts
projects (
    id              UUID PRIMARY KEY,
    account_id      UUID REFERENCES accounts(id),
    organization_id UUID REFERENCES organizations(id),
    name            VARCHAR,
    description     VARCHAR,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
)
```

### RBAC Tables

```sql
-- user_role_assignments: Maps users to roles on resources
user_role_assignments (
    user_id       INTEGER REFERENCES users(id),
    resource_id   UUID,
    role          VARCHAR CHECK (role IN ('superadmin', 'admin', 'editor', 'viewer')),
    resource_type VARCHAR CHECK (resource_type IN ('organization', 'account', 'project')),
    created_at    TIMESTAMP,
    PRIMARY KEY (user_id, resource_id)
)

-- permission_overrides: Fine-grained allow/deny rules
permission_overrides (
    user_id       INTEGER REFERENCES users(id),
    resource_id   UUID,
    resource_type VARCHAR,
    allow_actions JSONB,  -- ["edit_project", "delete_workflow"]
    deny_actions  JSONB,  -- ["execute_workflow"]
    created_at    TIMESTAMP,
    updated_at    TIMESTAMP,
    PRIMARY KEY (user_id, resource_id)
)
```

---

## Auth API Endpoints

### Check Access

```http
POST /api/auth/check-access
Content-Type: application/json

{
  "user_id": "user-123",
  "action": "edit_project",
  "resource": {
    "type": "project",
    "id": "proj-abc",
    "organization_id": "org-xyz",
    "account_id": "acc-456"
  }
}
```

**Response:**
```json
{ "allowed": true }
```

### Get User Permissions

```http
GET /api/auth/users/{user_id}/permissions
X-elevAIte-OrganizationId: org-xyz
```

**Response:**
```json
{
  "assignments": [
    { "role": "editor", "resource_type": "project", "resource_id": "proj-abc" }
  ],
  "overrides": {
    "allow": ["custom_action"],
    "deny": []
  }
}
```

---

## RBAC SDK Usage

### Installation

The SDK is available as `rbac-sdk` package.

### FastAPI Integration

```python
from fastapi import Depends, FastAPI
from rbac_sdk.fastapi_helpers import (
    require_permission,
    resource_builders,
    principal_resolvers,
)

app = FastAPI()

# Create a permission guard
project_view_guard = require_permission(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.user_id_header(),
)

@app.get("/projects/{project_id}", dependencies=[Depends(project_view_guard)])
def get_project(project_id: str):
    return {"project_id": project_id}
```

### Async Support

```python
from rbac_sdk.fastapi_helpers import require_permission_async

async_guard = require_permission_async(
    action="edit_project",
    resource_builder=resource_builders.project_from_headers(),
)

@app.post("/projects/{project_id}", dependencies=[Depends(async_guard)])
async def update_project(project_id: str):
    ...
```

### Required Headers

| Header | Description | Required |
|--------|-------------|----------|
| `X-elevAIte-UserId` | User identifier | Yes |
| `X-elevAIte-OrganizationId` | Organization context | Yes |
| `X-elevAIte-AccountId` | Account context | For account/project resources |
| `X-elevAIte-ProjectId` | Project context | For project resources |

### Calling a Protected Route

```http
GET /projects/proj-abc HTTP/1.1
Host: api.example.com
X-elevAIte-UserId: user-123
X-elevAIte-OrganizationId: org-xyz
X-elevAIte-AccountId: acc-456
X-elevAIte-ProjectId: proj-abc
```

**Success Response (200):**
```json
{ "project_id": "proj-abc" }
```

**Forbidden Response (403):**
```json
{ "detail": "Forbidden" }
```

**Missing Headers Response (400/401):**
```json
{ "detail": "Missing X-elevAIte-UserId header" }
```

---

## OPA Policy Logic

The policy evaluates in this order:

1. **Deny overrides** → Explicit deny always wins
2. **Allow overrides** → Explicit allow if not denied
3. **Role-based** → Check role assignments against resource hierarchy

### Resource Matching

| Role | Matches Resource If |
|------|---------------------|
| superadmin | `assignment.resource_id == resource.organization_id` |
| admin | `assignment.resource_id == resource.account_id` |
| editor/viewer | `assignment.resource_id == resource.id` (project) |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTH_API_BASE` | Base URL for Auth API | Required |
| `RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL` | Allow raw API key as principal (dev only) | `false` |
| `RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT` | Enable local JWT validation for API keys | `false` |
| `API_KEY_ALGORITHM` | JWT algorithm for API key validation | `HS256` |
| `API_KEY_SECRET` | Secret for HS256 API key validation | - |
| `API_KEY_PUBLIC_KEY` | Public key for RS/ES API key validation | - |

