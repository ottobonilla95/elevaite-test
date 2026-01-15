# RBAC API Guide

This guide covers the Role-Based Access Control (RBAC) system in the Auth API.

## Overview

The RBAC system uses a hierarchical permission model:

```
Organization → Account → Project
```

Users are assigned **roles** at specific resource levels, and can belong to **groups** that provide additional permissions or restrictions.

## Quick Start

### 1. Get Your RBAC Context

After login, fetch your complete RBAC info:

```bash
GET /api/rbac/me
Authorization: Bearer <token>
```

Returns your role assignments, group memberships, and permission overrides.

### 2. Check Access (Server-Side)

Use the authorization endpoint to verify access:

```bash
POST /api/authz/check
{
  "user_id": 123,
  "action": "view_project",
  "resource": {
    "type": "project",
    "id": "<project-uuid>",
    "organization_id": "<org-uuid>",
    "account_id": "<account-uuid>"
  }
}
```

## Roles

### System Roles

Four base role types are predefined (seeded via migration):

| Role | Permissions |
|------|-------------|
| `superadmin` | Full access (`*`) |
| `admin` | Create, read, update, delete, manage |
| `editor` | Create, read, update |
| `viewer` | Read only |

Each role exists at three scope levels: `organization`, `account`, `project`.

### Assigning Roles

```bash
POST /api/rbac/role-assignments
{
  "user_id": 123,
  "role_id": "<role-uuid>",
  "resource_id": "<org/account/project-uuid>",
  "resource_type": "organization"
}
```

### Listing Roles

```bash
GET /api/rbac/roles?scope_type=project&base_type=editor
```

## Groups

Groups are organization-defined permission sets that can **allow** or **deny** specific actions.

### Create a Group

```bash
POST /api/rbac/groups
{
  "organization_id": "<org-uuid>",
  "name": "Data Analysts",
  "description": "Read-only access to analytics"
}
```

### Add Permissions to a Group

```bash
POST /api/rbac/groups/<group-id>/permissions
{
  "service_name": "workflow_engine",
  "allow_actions": ["view_workflow", "run_workflow"],
  "deny_actions": ["delete_workflow"]
}
```

### Add Users to a Group

```bash
POST /api/rbac/groups/<group-id>/members
{
  "user_id": 123,
  "resource_id": "<project-uuid>",
  "resource_type": "project"
}
```

## Permission Overrides

For edge cases, apply per-user overrides on specific resources:

```bash
POST /api/rbac/permission-overrides
{
  "user_id": 123,
  "resource_id": "<project-uuid>",
  "resource_type": "project",
  "allow_actions": ["export_data"],
  "deny_actions": ["delete_project"]
}
```

## Permission Resolution Order

When checking access, permissions are evaluated in this order:

1. **Superuser** → Always allowed
2. **Explicit Deny** (override or group) → Denied
3. **Explicit Allow** (override) → Allowed
4. **Group Permissions** → Allow/Deny evaluated
5. **Role Permissions** → Based on assigned role at resource level
6. **Default** → Denied

## Common Patterns

### Give a user read-only access to a project

```bash
# Find the project_viewer role
GET /api/rbac/roles?scope_type=project&base_type=viewer

# Assign it
POST /api/rbac/role-assignments
{
  "user_id": 123,
  "role_id": "<project_viewer-role-id>",
  "resource_id": "<project-uuid>",
  "resource_type": "project"
}
```

### Restrict a user from deleting, even if they have editor role

```bash
POST /api/rbac/permission-overrides
{
  "user_id": 123,
  "resource_id": "<project-uuid>",
  "resource_type": "project",
  "deny_actions": ["delete_project", "delete_workflow"]
}
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rbac/me` | GET | Get current user's RBAC context |
| `/api/rbac/roles` | GET | List roles |
| `/api/rbac/roles/{id}` | GET | Get role details |
| `/api/rbac/role-assignments` | GET/POST | Manage role assignments |
| `/api/rbac/groups` | GET/POST | Manage groups |
| `/api/rbac/groups/{id}/permissions` | POST | Add group permissions |
| `/api/rbac/groups/{id}/members` | GET/POST | Manage group members |
| `/api/rbac/permission-overrides` | GET/POST | Manage user overrides |
| `/api/authz/check` | POST | Check if user has access |

