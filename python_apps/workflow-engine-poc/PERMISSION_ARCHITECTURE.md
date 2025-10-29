# Permission Management Architecture

This document provides a complete overview of the permission management system in the ElevAIte platform.

## Three Layers of Permission Management

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Role Assignments (WHO has WHICH role)            │
│  Managed by: Admins via Auth API                            │
│  Storage: Database (user_role_assignments table)           │
│  Scope: Per user, per resource                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Global Role Permissions (WHAT roles can DO)      │
│  Managed by: Superusers via Policy API                      │
│  Storage: OPA policy modules                                │
│  Scope: Global defaults for all resources                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Scoped Permissions (Resource-specific overrides) │
│  Managed by: Account/Project admins via Policy API          │
│  Storage: Database + OPA data                               │
│  Scope: Specific accounts or projects                       │
└─────────────────────────────────────────────────────────────┘
```

## Layer 1: Role Assignments

**Question:** "Which users have which roles on which resources?"

**Managed by:** Admins (anyone with admin role on a resource)

**API Endpoints:**
- `POST /api/rbac/user_role_assignments` - Assign role to user
- `GET /api/rbac/user_role_assignments` - List role assignments
- `DELETE /api/rbac/user_role_assignments/{user_id}/{resource_id}` - Remove role

**Example:**
```bash
# Assign editor role to user on a project
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "user_id": 123,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "project-uuid"
  }'
```

**Documentation:** [ADMIN_GUIDE.md](ADMIN_GUIDE.md)

## Layer 2: Global Role Permissions

**Question:** "What actions can each role perform globally?"

**Managed by:** Superusers only

**API Endpoints:**
- `POST /api/policies/generate` - Generate policy from role-action mappings
- `POST /api/policies/upload` - Upload custom Rego code
- `GET /api/policies` - List all policies
- `GET /api/policies/{module}` - Get specific policy
- `DELETE /api/policies/{module}` - Delete policy

**Example:**
```bash
# Set global permissions for workflow engine
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "actions": {
      "viewer": ["view_workflow"],
      "editor": ["view_workflow", "edit_workflow", "execute_workflow"],
      "admin": ["view_workflow", "edit_workflow", "execute_workflow", "delete_workflow"]
    }
  }'
```

**Documentation:** [DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md)

## Layer 3: Scoped Permissions (Future)

**Question:** "Can I customize permissions for my specific account or project?"

**Managed by:** Account admins (for their accounts) and Project admins (for their projects)

**API Endpoints (Proposed):**
- `POST /api/policies/scoped` - Set scoped permissions
- `GET /api/policies/scoped` - List scoped permissions
- `DELETE /api/policies/scoped/{id}` - Remove scoped permission

**Example (Proposed):**
```bash
# Account admin allows viewers to execute workflows in their account
curl -X POST http://localhost:8004/api/policies/scoped \
  -H "Authorization: Bearer $ACCOUNT_ADMIN_TOKEN" \
  -d '{
    "resource_type": "account",
    "resource_id": "account-uuid",
    "role": "viewer",
    "service_name": "workflow_engine",
    "allowed_actions": ["view_workflow", "execute_workflow"]
  }'
```

**Documentation:** [DELEGATED_PERMISSIONS.md](DELEGATED_PERMISSIONS.md)

## Permission Resolution Flow

```
User makes request → Workflow Engine
                          ↓
            Check RBAC (via RBAC SDK)
                          ↓
            Auth API gets user's role assignments
                          ↓
            OPA evaluates policy with precedence:
                          ↓
    ┌─────────────────────────────────────────┐
    │ 1. Check project-scoped permissions     │
    │    (if exists, use these)               │
    └─────────────────┬───────────────────────┘
                      ↓ (if not found)
    ┌─────────────────────────────────────────┐
    │ 2. Check account-scoped permissions     │
    │    (if exists, use these)               │
    └─────────────────┬───────────────────────┘
                      ↓ (if not found)
    ┌─────────────────────────────────────────┐
    │ 3. Use global role permissions          │
    │    (default for all resources)          │
    └─────────────────┬───────────────────────┘
                      ↓
            Return allow/deny decision
                      ↓
            Workflow Engine proceeds or rejects
```

## Who Can Manage What

| User Type | Can Manage | Scope | Documentation |
|-----------|------------|-------|---------------|
| **Superuser** | Role assignments | Any resource | [ADMIN_GUIDE.md](ADMIN_GUIDE.md) |
| | Global permissions | All resources | [DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md) |
| | Scoped permissions | Any resource | [DELEGATED_PERMISSIONS.md](DELEGATED_PERMISSIONS.md) |
| **Account Admin** | Role assignments | Their account + projects | [ADMIN_GUIDE.md](ADMIN_GUIDE.md) |
| | Scoped permissions | Their account + projects | [DELEGATED_PERMISSIONS.md](DELEGATED_PERMISSIONS.md) |
| **Project Admin** | Role assignments | Their project only | [ADMIN_GUIDE.md](ADMIN_GUIDE.md) |
| | Scoped permissions | Their project only | [DELEGATED_PERMISSIONS.md](DELEGATED_PERMISSIONS.md) |
| **Editor** | Nothing | N/A | N/A |
| **Viewer** | Nothing | N/A | N/A |

## Common Scenarios

### Scenario 1: Onboard New User

**Who:** Any admin (account admin, project admin, superuser)

**Steps:**
1. Create user account (or user registers)
2. Assign role to user on resource

**Example:**
```bash
# Assign viewer role to new user
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "user_id": 123,
    "role": "viewer",
    "resource_type": "project",
    "resource_id": "project-uuid"
  }'
```

**Result:** User can view the project (based on global viewer permissions)

### Scenario 2: Allow Viewers to Execute Workflows Globally

**Who:** Superuser only

**Steps:**
1. Update global policy to add execute_workflow to viewer actions

**Example:**
```bash
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -d '{
    "service_name": "workflow_engine",
    "actions": {
      "viewer": ["view_workflow", "execute_workflow"]
    }
  }'
```

**Result:** All viewers across all projects can execute workflows

### Scenario 3: Allow Viewers to Execute in Specific Account Only

**Who:** Account admin (or superuser)

**Steps:**
1. Create scoped permission for the account

**Example:**
```bash
curl -X POST http://localhost:8004/api/policies/scoped \
  -H "Authorization: Bearer $ACCOUNT_ADMIN_TOKEN" \
  -d '{
    "resource_type": "account",
    "resource_id": "account-uuid",
    "role": "viewer",
    "service_name": "workflow_engine",
    "allowed_actions": ["view_workflow", "execute_workflow"]
  }'
```

**Result:** Viewers in this account can execute workflows, but viewers in other accounts cannot

### Scenario 4: Restrict Editors in Specific Project

**Who:** Project admin (or account admin, or superuser)

**Steps:**
1. Create scoped permission for the project with restricted actions

**Example:**
```bash
curl -X POST http://localhost:8004/api/policies/scoped \
  -H "Authorization: Bearer $PROJECT_ADMIN_TOKEN" \
  -d '{
    "resource_type": "project",
    "resource_id": "project-uuid",
    "role": "editor",
    "service_name": "workflow_engine",
    "allowed_actions": ["view_workflow", "edit_workflow"]
  }'
```

**Result:** Editors in this project cannot execute or delete workflows (even if global policy allows it)

## Implementation Status

| Layer | Status | Documentation |
|-------|--------|---------------|
| **Layer 1: Role Assignments** | ✅ Implemented | [ADMIN_GUIDE.md](ADMIN_GUIDE.md) |
| **Layer 2: Global Permissions** | ✅ Implemented | [DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md) |
| **Layer 3: Scoped Permissions** | 📋 Planned | [DELEGATED_PERMISSIONS.md](DELEGATED_PERMISSIONS.md) |

## Workflow Engine Integration

### Current State

The workflow engine uses two main actions:
- `view_project` - Read-only operations (GET endpoints)
- `edit_project` - Write operations (POST, PUT, DELETE endpoints)

**Example guard:**
```python
from rbac_sdk.fastapi_helpers import require_permission_async

_guard_view = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(...),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

@router.get("/workflows")
async def list_workflows(_principal: str = Depends(_guard_view)):
    ...
```

### Recommended: Granular Actions

For better permission control, use specific actions:

```python
# Specific actions for different operations
_guard_view_workflow = require_permission_async(action="view_workflow", ...)
_guard_create_workflow = require_permission_async(action="create_workflow", ...)
_guard_edit_workflow = require_permission_async(action="edit_workflow", ...)
_guard_delete_workflow = require_permission_async(action="delete_workflow", ...)
_guard_execute_workflow = require_permission_async(action="execute_workflow", ...)

@router.get("/workflows")
async def list_workflows(_principal: str = Depends(_guard_view_workflow)):
    ...

@router.post("/workflows")
async def create_workflow(_principal: str = Depends(_guard_create_workflow)):
    ...

@router.post("/workflows/{id}/execute")
async def execute_workflow(_principal: str = Depends(_guard_execute_workflow)):
    ...
```

**Benefits:**
- Admins can allow viewers to execute but not edit
- Admins can allow editors to create/edit but not delete
- Fine-grained control over each operation

## Migration Guide

### Step 1: Update Workflow Engine Guards

Replace generic `view_project` and `edit_project` with specific actions:

```python
# Before
_guard_edit = require_permission_async(action="edit_project", ...)

# After
_guard_execute = require_permission_async(action="execute_workflow", ...)
```

### Step 2: Set Global Permissions

Define what each role can do globally:

```bash
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -d '{
    "service_name": "workflow_engine",
    "actions": {
      "viewer": ["view_workflow"],
      "editor": ["view_workflow", "edit_workflow", "create_workflow", "execute_workflow"],
      "admin": ["view_workflow", "edit_workflow", "create_workflow", "execute_workflow", "delete_workflow"]
    }
  }'
```

### Step 3: (Optional) Implement Scoped Permissions

Follow the implementation guide in [DELEGATED_PERMISSIONS.md](DELEGATED_PERMISSIONS.md) to enable account/project admins to customize permissions.

## Summary

The permission management system has three layers:

1. **Role Assignments** (✅ Implemented) - Admins assign roles to users
2. **Global Permissions** (✅ Implemented) - Superusers define what roles can do
3. **Scoped Permissions** (📋 Planned) - Account/Project admins customize for their resources

**Current capabilities:**
- ✅ Admins can assign roles to users
- ✅ Superusers can change global role permissions via API
- ✅ Changes take effect immediately (no redeployment)

**Future capabilities:**
- 📋 Account admins can customize permissions for their account
- 📋 Project admins can customize permissions for their project
- 📋 Hierarchical permission precedence (project > account > global)

**Next steps:**
1. Update workflow engine guards to use specific actions
2. Set global permissions for workflow engine
3. (Optional) Implement scoped permissions for delegated management

