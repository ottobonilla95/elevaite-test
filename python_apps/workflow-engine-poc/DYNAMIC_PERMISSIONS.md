# Dynamic Permission Management - Changing Role Permissions via API

This guide explains how to dynamically change what roles can do in the Workflow Engine **without modifying code or redeploying**.

## Overview

The Auth API already has **dynamic policy management** built in! You can:

✅ Change role permissions via API  
✅ Add new actions for existing roles  
✅ Create custom roles with specific permissions  
✅ Upload custom Rego policies  
✅ No code changes or redeployment needed  

## How It Works

```
┌─────────────────────────────────────────┐
│         Admin / Superuser               │
│  "Allow viewers to execute workflows"   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Auth API - Policy Management       │
│      POST /api/policies/generate        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         OPA Policy API                  │
│    PUT /v1/policies/rbac/workflows      │
│    (Updates policy in memory)           │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Workflow Engine PoC                │
│  Uses updated permissions immediately   │
└─────────────────────────────────────────┘
```

**Key Point:** Changes take effect immediately - no restart required!

## Prerequisites

1. **Superuser Access** - Only superusers can manage policies
2. **Auth API Running** - Default: `http://localhost:8004`
3. **OPA Running** - Default: `http://localhost:8181`

## Available Endpoints

### 1. Generate Service Policy

**Endpoint:** `POST /api/policies/generate`

Generate and upload a policy for a service based on role-action mappings.

**Request:**
```json
{
  "service_name": "workflow_engine",
  "resource_type": "workflow",
  "belongs_to": "project",
  "actions": {
    "superadmin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
    "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
    "editor": ["create_workflow", "edit_workflow", "view_workflow", "execute_workflow"],
    "viewer": ["view_workflow"]
  }
}
```

**Parameters:**
- `service_name` - Name of the service (e.g., "workflow_engine")
- `resource_type` - Type of resource (e.g., "workflow")
- `belongs_to` - What the resource belongs to: "organization", "account", or "project"
- `actions` - Dictionary mapping role names to lists of allowed actions

### 2. Upload Custom Policy

**Endpoint:** `POST /api/policies/upload`

Upload custom Rego code directly.

**Request:**
```json
{
  "module_name": "rbac/custom_workflows",
  "rego_code": "package rbac\n\nimport rego.v1\n\nrole_check(assignment) if {\n  assignment.role == \"analyst\"\n  input.action == \"export_workflow\"\n}"
}
```

### 3. List Policies

**Endpoint:** `GET /api/policies`

List all policy modules currently loaded in OPA.

### 4. Get Policy

**Endpoint:** `GET /api/policies/{module_name}`

Get the Rego code for a specific policy module.

### 5. Delete Policy

**Endpoint:** `DELETE /api/policies/{module_name}`

Delete a policy module from OPA.

## Common Scenarios

### Scenario 1: Allow Viewers to Execute Workflows

**Current:** Viewers can only view workflows  
**Goal:** Allow viewers to execute workflows but not modify them

```bash
# Login as superuser
curl -X POST http://localhost:8004/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superuser@elevaite.com",
    "password": "superuser123"
  }'

export SUPERUSER_TOKEN="<access_token>"

# Generate new policy with execute permission for viewers
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "belongs_to": "project",
    "actions": {
      "superadmin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
      "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
      "editor": ["create_workflow", "edit_workflow", "view_workflow", "execute_workflow"],
      "viewer": ["view_workflow", "execute_workflow"]
    }
  }'
```

**Result:** Viewers can now execute workflows immediately!

### Scenario 2: Restrict Editors from Deleting

**Current:** Editors can create, update, delete, execute  
**Goal:** Editors can create/update/execute but not delete

```bash
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "belongs_to": "project",
    "actions": {
      "superadmin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
      "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
      "editor": ["create_workflow", "edit_workflow", "view_workflow", "execute_workflow"],
      "viewer": ["view_workflow"]
    }
  }'
```

**Note:** You'll also need to update the workflow engine guards to use `delete_workflow` action instead of `edit_project`.

### Scenario 3: Create Custom "Analyst" Role

**Goal:** Create a new "analyst" role that can view and execute but not create/edit

```bash
curl -X POST http://localhost:8004/api/policies/upload \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "rbac/analyst_role",
    "rego_code": "package rbac\n\nimport rego.v1\n\n# Analyst can view and execute workflows\nrole_check(assignment) if {\n  assignment.role == \"analyst\"\n  input.resource.type == \"workflow\"\n  input.action in {\"view_workflow\", \"execute_workflow\"}\n}\n\n# Analyst resource matching\nvalid_resource_match(assignment) if {\n  assignment.role == \"analyst\"\n  assignment.resource_type == \"project\"\n  input.resource.project_id == assignment.resource_id\n}"
  }'
```

Then assign the analyst role to users:

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

### Scenario 4: Per-Client Custom Permissions

**Goal:** Different clients have different permissions for the same role

**Option A: Use separate policy modules per client**

```bash
# Client A: Viewers can execute
curl -X POST http://localhost:8004/api/policies/upload \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "rbac/client_a_workflows",
    "rego_code": "package rbac\n\nimport rego.v1\n\nrole_check(assignment) if {\n  assignment.role == \"viewer\"\n  input.resource.type == \"workflow\"\n  input.resource.organization_id == \"client-a-org-uuid\"\n  input.action in {\"view_workflow\", \"execute_workflow\"}\n}"
  }'

# Client B: Viewers can only view
curl -X POST http://localhost:8004/api/policies/upload \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "rbac/client_b_workflows",
    "rego_code": "package rbac\n\nimport rego.v1\n\nrole_check(assignment) if {\n  assignment.role == \"viewer\"\n  input.resource.type == \"workflow\"\n  input.resource.organization_id == \"client-b-org-uuid\"\n  input.action == \"view_workflow\"\n}"
  }'
```

**Option B: Use organization-specific metadata**

Store custom permissions in the database and check them in the policy:

```rego
package rbac

import rego.v1

# Check organization-specific permissions
role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "workflow"
    
    # Get org-specific permissions from data
    org_permissions := data.org_permissions[input.resource.organization_id]
    viewer_actions := org_permissions.viewer_actions
    
    input.action in viewer_actions
}
```

Then load organization permissions as data:

```bash
curl -X PUT http://localhost:8181/v1/data/org_permissions \
  -H "Content-Type: application/json" \
  -d '{
    "client-a-org-uuid": {
      "viewer_actions": ["view_workflow", "execute_workflow"]
    },
    "client-b-org-uuid": {
      "viewer_actions": ["view_workflow"]
    }
  }'
```

## Testing Permission Changes

### 1. Verify Policy is Loaded

```bash
# List all policies
curl -X GET http://localhost:8004/api/policies \
  -H "Authorization: Bearer $SUPERUSER_TOKEN"

# Get specific policy
curl -X GET http://localhost:8004/api/policies/rbac/workflow_engine \
  -H "Authorization: Bearer $SUPERUSER_TOKEN"
```

### 2. Test Authorization

```bash
# Check if viewer can execute workflow
curl -X POST http://localhost:8004/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "action": "execute_workflow",
    "resource": {
      "type": "workflow",
      "id": "workflow-uuid",
      "project_id": "project-uuid",
      "account_id": "account-uuid",
      "organization_id": "org-uuid"
    }
  }'
```

### 3. Test with Workflow Engine

```bash
# Try to execute a workflow as a viewer
curl -X POST http://localhost:8006/workflows/workflow-uuid/execute \
  -H "X-elevAIte-apikey: $VIEWER_API_KEY" \
  -H "X-elevAIte-ProjectId: $PROJECT_ID" \
  -H "X-elevAIte-AccountId: $ACCOUNT_ID" \
  -H "X-elevAIte-OrganizationId: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Important Notes

### Mapping Actions to Workflow Engine Guards

The workflow engine currently uses two main actions:
- `view_project` - Read-only operations
- `edit_project` - Create, update, delete, execute operations

**To use granular actions like `execute_workflow`, you need to:**

1. **Update the workflow engine guards** to use specific actions:

```python
# In workflow_engine_poc/routers/workflows.py

_guard_execute_workflow = require_permission_async(
    action="execute_workflow",  # Changed from "edit_project"
    resource_builder=resource_builders.project_from_headers(...),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

@router.post("/workflows/{id}/execute")
async def execute_workflow(
    id: UUID,
    _principal: str = Depends(_guard_execute_workflow),  # Use specific guard
    ...
):
    ...
```

2. **Generate the policy with the new actions**:

```bash
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "belongs_to": "project",
    "actions": {
      "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow", "execute_workflow"],
      "editor": ["create_workflow", "edit_workflow", "view_workflow", "execute_workflow"],
      "viewer": ["view_workflow", "execute_workflow"]
    }
  }'
```

### Policy Module Naming

- Use `rbac/` prefix for all policy modules
- Use descriptive names: `rbac/workflow_engine`, `rbac/custom_rules`
- Avoid conflicts with core policy: `rbac/rbac` (the main policy file)

### Policy Persistence

**Important:** Policies uploaded via API are stored **in OPA's memory only**. They will be lost if OPA restarts.

**Solutions:**

1. **Re-upload on startup** - Add a startup script to reload policies
2. **Store in database** - Save policies in PostgreSQL and reload on startup
3. **Use OPA bundles** - Configure OPA to load policies from a bundle server

## Troubleshooting

### Issue: Policy changes not taking effect

**Check:**
1. Policy was uploaded successfully (check response)
2. OPA is running: `curl http://localhost:8181/health`
3. Policy syntax is valid: `curl http://localhost:8004/api/policies/rbac/workflow_engine`

### Issue: "Failed to upload policy to OPA"

**Causes:**
- OPA is not running
- OPA URL is incorrect
- Rego syntax error

**Solution:**
```bash
# Check OPA is running
curl http://localhost:8181/health

# Check OPA URL in Auth API
echo $OPA_URL  # Should be http://localhost:8181
```

### Issue: Custom role not working

**Check:**
1. Policy includes both `role_check` and `valid_resource_match` rules
2. Role name matches exactly (case-sensitive)
3. Resource type matches what the workflow engine sends

## Summary

**Yes, you can change role permissions remotely via API!**

**Steps:**
1. Login as superuser
2. Call `POST /api/policies/generate` with new action mappings
3. Changes take effect immediately
4. No code changes or redeployment needed

**For more advanced scenarios:**
- Upload custom Rego code with `POST /api/policies/upload`
- Use organization-specific policies
- Store permissions in database and reference in policy

**See Also:**
- [Auth API Policy Management Docs](../auth_api/docs/DYNAMIC_POLICY_MANAGEMENT.md)
- [OPA Policy Guide](../auth_api/docs/OPA_POLICY_GUIDE.md)
- [ROLE_PERMISSIONS.md](ROLE_PERMISSIONS.md) - Understanding the policy structure

