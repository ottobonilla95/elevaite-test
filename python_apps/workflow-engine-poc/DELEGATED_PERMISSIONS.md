# Delegated Permission Management

This guide explains how to enable **delegated permission management** where lower-level admins (account admins, project admins) can set permissions for resources they manage.

## Overview

The current system has two levels of permission management:

1. **Role Assignments** - WHO has WHICH role (managed by admins via Auth API)
2. **Role Permissions** - WHAT each role can DO (managed by superusers via policy API)

**Problem:** Currently, only superusers can change role permissions (what roles can do). Account admins and project admins cannot customize permissions for their specific resources.

**Solution:** Enable **scoped policy management** where admins can set permissions for their scope only.

## Architecture Options

### Option 1: Resource-Scoped Policies (Recommended) ⭐

Allow admins to create policies scoped to their specific resources (account or project).

**How it works:**

```
┌─────────────────────────────────────────┐
│      Superuser (Organization)           │
│  Sets global default permissions        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Account Admin (Account)            │
│  Overrides permissions for account      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Project Admin (Project)            │
│  Overrides permissions for project      │
└─────────────────────────────────────────┘
```

**OPA Policy Structure:**

```rego
package rbac

import rego.v1

# Default permissions (set by superuser)
default_permissions := {
    "viewer": ["view_workflow"],
    "editor": ["view_workflow", "edit_workflow"]
}

# Account-specific overrides (set by account admins)
account_permissions := data.account_permissions

# Project-specific overrides (set by project admins)
project_permissions := data.project_permissions

# Permission resolution with precedence
allowed_actions(role, resource) := actions if {
    # 1. Check project-specific permissions first
    project_perms := project_permissions[resource.project_id]
    actions := project_perms[role]
} else := actions if {
    # 2. Check account-specific permissions
    account_perms := account_permissions[resource.account_id]
    actions := account_perms[role]
} else := actions if {
    # 3. Fall back to default permissions
    actions := default_permissions[role]
}

# Role check using resolved permissions
role_check(assignment) if {
    actions := allowed_actions(assignment.role, input.resource)
    input.action in actions
}
```

**Benefits:**
- ✅ Hierarchical permission management
- ✅ Project admins can customize for their projects
- ✅ Account admins can set defaults for all projects in account
- ✅ Superusers can set global defaults
- ✅ Clear precedence: project > account > global

**Drawbacks:**
- ⚠️ More complex policy logic
- ⚠️ Need to store permission overrides in database or OPA data

### Option 2: Permission Templates (Simpler Alternative)

Provide pre-defined permission templates that admins can assign to their resources.

**How it works:**

```bash
# Superuser creates templates
curl -X POST http://localhost:8004/api/policies/templates \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -d '{
    "template_name": "restrictive",
    "permissions": {
      "viewer": ["view_workflow"],
      "editor": ["view_workflow", "edit_workflow"]
    }
  }'

curl -X POST http://localhost:8004/api/policies/templates \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -d '{
    "template_name": "permissive",
    "permissions": {
      "viewer": ["view_workflow", "execute_workflow"],
      "editor": ["view_workflow", "edit_workflow", "execute_workflow", "delete_workflow"]
    }
  }'

# Account admin assigns template to their account
curl -X POST http://localhost:8004/api/policies/assign_template \
  -H "Authorization: Bearer $ACCOUNT_ADMIN_TOKEN" \
  -d '{
    "resource_type": "account",
    "resource_id": "account-uuid",
    "template_name": "permissive"
  }'
```

**Benefits:**
- ✅ Simpler to implement
- ✅ Admins choose from pre-approved templates
- ✅ Easier to audit and maintain
- ✅ Less risk of misconfiguration

**Drawbacks:**
- ⚠️ Less flexible than custom policies
- ⚠️ Admins can't create custom permission sets

### Option 3: Action-Level Delegation

Allow admins to enable/disable specific actions for roles in their scope.

**How it works:**

```bash
# Account admin enables execute_workflow for viewers in their account
curl -X POST http://localhost:8004/api/policies/permissions \
  -H "Authorization: Bearer $ACCOUNT_ADMIN_TOKEN" \
  -d '{
    "resource_type": "account",
    "resource_id": "account-uuid",
    "role": "viewer",
    "action": "execute_workflow",
    "enabled": true
  }'
```

**Benefits:**
- ✅ Fine-grained control
- ✅ Simple UI (checkboxes for each action)
- ✅ Easy to understand

**Drawbacks:**
- ⚠️ Can become complex with many actions
- ⚠️ Need to track many individual permissions

## Recommended Implementation: Option 1 (Resource-Scoped Policies)

### Step 1: Add Permission Override Storage

Create a table to store permission overrides:

```sql
CREATE TABLE permission_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR NOT NULL CHECK (resource_type IN ('organization', 'account', 'project')),
    resource_id UUID NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('superadmin', 'admin', 'editor', 'viewer')),
    service_name VARCHAR NOT NULL,  -- e.g., 'workflow_engine'
    allowed_actions JSONB NOT NULL,  -- e.g., ["view_workflow", "execute_workflow"]
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(resource_type, resource_id, role, service_name)
);

CREATE INDEX idx_permission_overrides_resource ON permission_overrides(resource_type, resource_id);
CREATE INDEX idx_permission_overrides_service ON permission_overrides(service_name);
```

### Step 2: Add API Endpoints for Delegated Management

```python
# python_apps/auth_api/app/routers/policies.py

@router.post("/policies/scoped", response_model=MessageResponse)
async def set_scoped_permissions(
    data: ScopedPermissionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_tenant_async_db),
    policy_service: PolicyService = Depends(get_policy_service),
):
    """
    Set permissions for a specific resource scope.
    
    - Superusers can set permissions for any resource
    - Account admins can set permissions for their accounts and projects
    - Project admins can set permissions for their projects only
    
    This creates a permission override that takes precedence over global defaults.
    """
    # Step 1: Verify user has admin access to the resource
    await verify_admin_access(current_user, data.resource_type, data.resource_id, session)
    
    # Step 2: Store permission override in database
    override = PermissionOverride(
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        role=data.role,
        service_name=data.service_name,
        allowed_actions=data.allowed_actions,
        created_by=current_user.id,
    )
    session.add(override)
    await session.commit()
    
    # Step 3: Reload OPA data with new overrides
    await reload_opa_permission_data(session, policy_service)
    
    return MessageResponse(
        message=f"Permissions updated for {data.role} on {data.resource_type} {data.resource_id}"
    )


async def verify_admin_access(
    user: User,
    resource_type: str,
    resource_id: UUID,
    session: AsyncSession,
):
    """Verify user has admin access to the resource."""
    if user.is_superuser:
        return  # Superusers can manage any resource
    
    # Check if user has admin role on the resource
    query = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user.id,
        UserRoleAssignment.resource_id == resource_id,
        UserRoleAssignment.role == "admin",
    )
    result = await session.execute(query)
    assignment = result.scalars().first()
    
    if not assignment:
        # Check if user has admin role on parent account (for project resources)
        if resource_type == "project":
            # Get project's account_id
            project_query = select(Project).where(Project.id == resource_id)
            project_result = await session.execute(project_query)
            project = project_result.scalars().first()
            
            if project:
                # Check admin role on account
                account_query = select(UserRoleAssignment).where(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.resource_id == project.account_id,
                    UserRoleAssignment.role == "admin",
                )
                account_result = await session.execute(account_query)
                account_assignment = account_result.scalars().first()
                
                if account_assignment:
                    return
        
        raise HTTPException(
            status_code=403,
            detail=f"User does not have admin access to {resource_type} {resource_id}",
        )


async def reload_opa_permission_data(
    session: AsyncSession,
    policy_service: PolicyService,
):
    """Load all permission overrides into OPA data."""
    # Get all permission overrides
    query = select(PermissionOverride)
    result = await session.execute(query)
    overrides = result.scalars().all()
    
    # Group by resource type and ID
    account_permissions = {}
    project_permissions = {}
    
    for override in overrides:
        if override.resource_type == "account":
            if override.resource_id not in account_permissions:
                account_permissions[str(override.resource_id)] = {}
            account_permissions[str(override.resource_id)][override.role] = override.allowed_actions
        elif override.resource_type == "project":
            if override.resource_id not in project_permissions:
                project_permissions[str(override.resource_id)] = {}
            project_permissions[str(override.resource_id)][override.role] = override.allowed_actions
    
    # Upload to OPA data API
    await policy_service.upload_data("account_permissions", account_permissions)
    await policy_service.upload_data("project_permissions", project_permissions)
```

### Step 3: Update OPA Policy to Use Scoped Permissions

The policy needs to check for resource-specific overrides:

```rego
package rbac

import rego.v1

# Permission resolution with precedence: project > account > global
allowed_actions(role, resource) := actions if {
    # 1. Check project-specific permissions first
    project_id := resource.project_id
    project_perms := data.project_permissions[project_id]
    actions := project_perms[role]
} else := actions if {
    # 2. Check account-specific permissions
    account_id := resource.account_id
    account_perms := data.account_permissions[account_id]
    actions := account_perms[role]
} else := actions if {
    # 3. Fall back to default permissions (from global policy)
    actions := default_permissions[role]
}

# Default permissions (can be overridden by scoped permissions)
default_permissions := {
    "viewer": ["view_workflow"],
    "editor": ["view_workflow", "edit_workflow"],
    "admin": ["view_workflow", "edit_workflow", "delete_workflow", "execute_workflow"],
    "superadmin": ["view_workflow", "edit_workflow", "delete_workflow", "execute_workflow"]
}

# Role check using resolved permissions
role_check(assignment) if {
    actions := allowed_actions(assignment.role, input.resource)
    input.action in actions
}
```

## Usage Examples

### Example 1: Account Admin Enables Viewer Execution

```bash
# Login as account admin
curl -X POST http://localhost:8004/api/auth/login \
  -d '{"email": "account-admin@company.com", "password": "password"}'

export ACCOUNT_ADMIN_TOKEN="<access_token>"

# Set permissions for viewers in this account
curl -X POST http://localhost:8004/api/policies/scoped \
  -H "Authorization: Bearer $ACCOUNT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "account",
    "resource_id": "account-uuid",
    "role": "viewer",
    "service_name": "workflow_engine",
    "allowed_actions": ["view_workflow", "execute_workflow"]
  }'
```

**Result:** All viewers in this account (and its projects) can now execute workflows.

### Example 2: Project Admin Restricts Editors

```bash
# Login as project admin
curl -X POST http://localhost:8004/api/auth/login \
  -d '{"email": "project-admin@company.com", "password": "password"}'

export PROJECT_ADMIN_TOKEN="<access_token>"

# Restrict editors in this project (no delete)
curl -X POST http://localhost:8004/api/policies/scoped \
  -H "Authorization: Bearer $PROJECT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "project",
    "resource_id": "project-uuid",
    "role": "editor",
    "service_name": "workflow_engine",
    "allowed_actions": ["view_workflow", "edit_workflow", "execute_workflow"]
  }'
```

**Result:** Editors in this specific project cannot delete workflows (even if account-level policy allows it).

## Security Considerations

1. **Privilege Escalation Prevention**
   - Admins cannot grant permissions they don't have
   - Admins cannot modify permissions for higher-level resources
   - Superusers can override any scoped permissions

2. **Audit Trail**
   - All permission changes logged with `created_by` user ID
   - Track when permissions were changed
   - Can query who changed what permissions

3. **Validation**
   - Validate that actions exist in the service
   - Prevent typos in action names
   - Ensure role names are valid

4. **Scope Enforcement**
   - Account admins can only manage their account and its projects
   - Project admins can only manage their specific project
   - Superusers can manage any resource

## Migration Path

1. **Phase 1: Add database schema** for permission overrides
2. **Phase 2: Add API endpoints** for scoped permission management
3. **Phase 3: Update OPA policy** to check scoped permissions
4. **Phase 4: Add UI** for admins to manage permissions
5. **Phase 5: Migrate existing** custom policies to scoped model

## Summary

**Delegated permission management enables:**

✅ **Account admins** can customize permissions for their account  
✅ **Project admins** can customize permissions for their project  
✅ **Hierarchical precedence**: project > account > global  
✅ **Audit trail** of all permission changes  
✅ **Security**: admins can only manage resources they control  

This provides flexibility while maintaining security and auditability.

