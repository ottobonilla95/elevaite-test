# Role Permissions Configuration

This document explains how role permissions are defined and how to modify what each role can access.

## Overview

The RBAC system has **two separate concerns**:

1. **Role Assignments** (Database) - Which users have which roles on which resources
2. **Role Permissions** (OPA Policy) - What actions each role is allowed to perform

**Key Point:** Admins assign roles to users via the Auth API, but the **permissions for each role are defined in the OPA policy**.

## Two Ways to Change Role Permissions

### Option 1: Dynamic API Management (Recommended) ⚡

**Change permissions via API without code changes or redeployment!**

See [DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md) for complete guide.

**Quick example:**
```bash
# Allow viewers to execute workflows
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "actions": {
      "viewer": ["view_workflow", "execute_workflow"]
    }
  }'
```

**Benefits:**
- ✅ Changes take effect immediately
- ✅ No code changes needed
- ✅ No redeployment needed
- ✅ Can be done by superusers via API

### Option 2: Edit OPA Policy File (Traditional) 🔧

**Modify the Rego policy file directly (requires code deployment)**

This document covers this approach in detail below.

## How It Works

### 1. Role Assignments (Database)

Admins manage **who has what role** through the Auth API:

```bash
# Assign a role to a user
POST /api/rbac/user_role_assignments
{
  "user_id": 123,
  "role": "editor",
  "resource_type": "project",
  "resource_id": "project-uuid"
}
```

This is stored in the database and determines which roles a user has.

### 2. Role Permissions (OPA Policy)

The **permissions for each role** are defined in the OPA policy file at:

**`python_apps/auth_api/policies/rbac.rego`**

This policy defines what actions each role can perform.

## Current Role Permissions

Based on the OPA policy, here are the current permissions:

### Superadmin (Organization Level)

```rego
role_check(assignment) if {
    assignment.role == "superadmin"
}
```

**Permissions:**
- ✅ **ALL actions** on ALL resources in the organization
- No restrictions

**Use case:** Company owner, CTO, platform administrator

---

### Admin (Account Level)

```rego
role_check(assignment) if {
    assignment.role == "admin"
    input.resource.type in {"account", "project"}
    input.action in {"manage_account", "edit_project", "view_project"}
}
```

**Permissions:**
- ✅ `manage_account` - Manage account settings and users
- ✅ `edit_project` - Create, update, delete, execute workflows
- ✅ `view_project` - View workflows and results

**Applies to:** All projects within the account

**Use case:** Department head, team lead

---

### Editor (Project Level)

```rego
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "project"
    input.action in {"edit_project", "view_project"}
}
```

**Permissions:**
- ✅ `edit_project` - Create, update, delete, execute workflows
- ✅ `view_project` - View workflows and results
- ❌ `manage_account` - Cannot manage account settings

**Applies to:** Only the specific project assigned

**Use case:** Developer, workflow creator, power user

---

### Viewer (Project Level)

```rego
role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "project"
    input.action == "view_project"
}
```

**Permissions:**
- ✅ `view_project` - View workflows and results
- ❌ `edit_project` - Cannot create, update, delete, or execute
- ❌ `manage_account` - Cannot manage account settings

**Applies to:** Only the specific project assigned

**Use case:** Stakeholder, auditor, read-only user

## How to Change Role Permissions

### Option 1: Modify the OPA Policy (Recommended)

To change what a role can do, edit the OPA policy file:

**File:** `python_apps/auth_api/policies/rbac.rego`

#### Example: Allow Viewers to Execute Workflows

Currently, viewers can only view. To allow them to execute workflows, you would need to:

1. **Define a new action** (if needed):
   ```rego
   # In your workflow engine guards, add a new action
   action = "execute_workflow"
   ```

2. **Update the viewer role_check**:
   ```rego
   role_check(assignment) if {
       assignment.role == "viewer"
       input.resource.type == "project"
       input.action in {"view_project", "execute_workflow"}  # Added execute_workflow
   }
   ```

3. **Reload the OPA policy**:
   ```bash
   # OPA automatically reloads when the file changes
   # Or restart OPA if using Docker
   docker restart opa
   ```

#### Example: Create a New "Analyst" Role

To add a new role with custom permissions:

1. **Add the role_check rule**:
   ```rego
   role_check(assignment) if {
       assignment.role == "analyst"
       input.resource.type == "project"
       input.action in {"view_project", "execute_workflow", "view_analytics"}
   }
   ```

2. **Add resource matching** (if needed):
   ```rego
   valid_resource_match(assignment) if {
       assignment.role == "analyst"
       assignment.resource_type == "project"
       input.resource.id == assignment.resource_id
   }
   ```

3. **Update the database schema** (if needed):
   ```python
   # In your role enum/validation
   VALID_ROLES = ["superadmin", "admin", "editor", "viewer", "analyst"]
   ```

4. **Assign the new role to users**:
   ```bash
   curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 123,
       "role": "analyst",
       "resource_type": "project",
       "resource_id": "project-uuid"
     }'
   ```

### Option 2: Create Action-Specific Permissions

Instead of modifying role permissions, you can create more granular actions:

#### Current Actions:
- `view_project` - Read-only access
- `edit_project` - Full write access
- `manage_account` - Account management

#### Example: Split `edit_project` into Granular Actions

```rego
# Allow editors to create and update, but not delete
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "project"
    input.action in {"view_project", "create_workflow", "update_workflow", "execute_workflow"}
}

# Only admins can delete
role_check(assignment) if {
    assignment.role == "admin"
    input.resource.type in {"account", "project"}
    input.action in {"manage_account", "view_project", "create_workflow", "update_workflow", "execute_workflow", "delete_workflow"}
}
```

Then update your workflow engine guards:

```python
# In workflows.py
_guard_delete_workflow = require_permission_async(
    action="delete_workflow",  # Changed from "edit_project"
    resource_builder=resource_builders.project_from_headers(...),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

@router.delete("/workflows/{id}")
async def delete_workflow(
    id: UUID,
    _principal: str = Depends(_guard_delete_workflow),  # Now requires delete_workflow
    ...
):
    ...
```

## Testing Permission Changes

After modifying the OPA policy, test the changes:

### 1. Test with OPA Directly

```bash
# Test a permission check
curl -X POST http://localhost:8181/v1/data/rbac/allow \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "user": {
        "id": 123,
        "status": "active",
        "assignments": [
          {
            "role": "viewer",
            "resource_type": "project",
            "resource_id": "project-uuid"
          }
        ]
      },
      "action": "view_project",
      "resource": {
        "type": "project",
        "id": "project-uuid",
        "account_id": "account-uuid",
        "organization_id": "org-uuid"
      }
    }
  }'
```

Expected response:
```json
{
  "result": true  // or false if denied
}
```

### 2. Test with Auth API

```bash
curl -X POST http://localhost:8004/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "action": "view_project",
    "resource": {
      "type": "project",
      "id": "project-uuid",
      "account_id": "account-uuid",
      "organization_id": "org-uuid"
    }
  }'
```

### 3. Test with Workflow Engine

```bash
# Try to access an endpoint with the modified permissions
curl -X GET http://localhost:8006/workflows/ \
  -H "X-elevAIte-apikey: $API_KEY" \
  -H "X-elevAIte-ProjectId: $PROJECT_ID" \
  -H "X-elevAIte-AccountId: $ACCOUNT_ID" \
  -H "X-elevAIte-OrganizationId: $ORG_ID"
```

### 4. Run Automated Tests

```bash
cd python_apps/workflow-engine-poc
pytest tests/test_rbac_e2e.py -v
```

## Common Permission Modifications

### Scenario 1: Allow Viewers to Execute Workflows

**Current:** Viewers can only view workflows  
**Goal:** Allow viewers to execute workflows but not modify them

**Change in `rbac.rego`:**
```rego
role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "project"
    input.action in {"view_project", "edit_project"}  # Add edit_project for execute
}
```

**Note:** This gives viewers full edit access. For execute-only, create a new `execute_workflow` action.

### Scenario 2: Restrict Editors from Deleting

**Current:** Editors can create, update, delete, execute  
**Goal:** Editors can create/update/execute but not delete

**Changes needed:**

1. **Split actions in guards:**
   ```python
   # Create separate guards
   _guard_delete_project = require_permission_async(action="delete_workflow", ...)
   _guard_create_project = require_permission_async(action="create_workflow", ...)
   ```

2. **Update OPA policy:**
   ```rego
   role_check(assignment) if {
       assignment.role == "editor"
       input.resource.type == "project"
       input.action in {"view_project", "create_workflow", "update_workflow", "execute_workflow"}
   }
   
   role_check(assignment) if {
       assignment.role == "admin"
       input.resource.type in {"account", "project"}
       input.action in {"manage_account", "view_project", "create_workflow", "update_workflow", "execute_workflow", "delete_workflow"}
   }
   ```

### Scenario 3: Add Department-Level Role

**Goal:** Create a "department_admin" role between account admin and project editor

**Add to `rbac.rego`:**
```rego
valid_resource_match(assignment) if {
    assignment.role == "department_admin"
    assignment.resource_type == "account"
    assignment.resource_id == input.resource.account_id
}

role_check(assignment) if {
    assignment.role == "department_admin"
    input.resource.type in {"account", "project"}
    input.action in {"edit_project", "view_project"}  # Can edit but not manage account
}
```

## Best Practices

1. **Keep Roles Simple** - Don't create too many roles; use 4-6 well-defined roles
2. **Use Granular Actions** - Instead of modifying role permissions, create specific actions
3. **Test Thoroughly** - Always test permission changes with automated tests
4. **Document Changes** - Update this document when modifying the policy
5. **Version Control** - Commit OPA policy changes with clear commit messages
6. **Fail Closed** - Default to denying access; explicitly allow what's needed

## OPA Policy Structure

The policy has three main parts:

### 1. Default Deny
```rego
default allow := false
```
Everything is denied unless explicitly allowed.

### 2. Resource Matching
```rego
valid_resource_match(assignment) if {
    # Check if user's role assignment matches the resource being accessed
}
```
Ensures the user's role applies to the resource they're trying to access.

### 3. Role Checks
```rego
role_check(assignment) if {
    # Check if the role has permission for the requested action
}
```
Defines what actions each role can perform.

## Summary

**To change what a role can access:**

1. **Edit the OPA policy** at `python_apps/auth_api/policies/rbac.rego`
2. **Modify the `role_check` rules** for the role you want to change
3. **Add new actions** if you need more granular control
4. **Test the changes** with OPA, Auth API, and Workflow Engine
5. **Update documentation** to reflect the new permissions
6. **Commit the changes** with a clear commit message

**Admins do NOT change role permissions through the API** - they only assign roles to users. The permissions for each role are defined in the OPA policy file and require code changes to modify.

