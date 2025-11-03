# RBAC API Completeness Audit

**Date:** 2025-11-03  
**Status:** ✅ MOSTLY COMPLETE - Missing Permission Overrides

## Executive Summary

The Auth API has a **comprehensive RBAC implementation** with role assignments fully functional. However, **permission overrides are NOT implemented** in the Auth API, though they exist in the legacy `python_apps/rbac` service.

## 1. ✅ Role Assignment Endpoints (COMPLETE)

### Implemented in `python_apps/auth_api/app/routers/rbac.py`

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/rbac/user_role_assignments` | POST | ✅ Complete | Create/update role assignment |
| `/api/rbac/user_role_assignments` | GET | ✅ Complete | List role assignments with filters |
| `/api/rbac/user_role_assignments/{user_id}/{resource_id}` | DELETE | ✅ Complete | Delete role assignment |

### Features

**Create/Update Role Assignment** (Lines 355-445):
- ✅ Validates user exists
- ✅ Validates resource exists (organization/account/project)
- ✅ Checks for existing assignment (upsert behavior)
- ✅ Requires superuser (TODO: should allow admins on resource)
- ✅ Supports all role types: `superadmin`, `admin`, `editor`, `viewer`
- ✅ Supports all resource types: `organization`, `account`, `project`

**List Role Assignments** (Lines 448-489):
- ✅ Filter by `user_id`
- ✅ Filter by `resource_id`
- ✅ Filter by `resource_type`
- ✅ Pagination with `skip` and `limit`
- ✅ Returns total count

**Delete Role Assignment** (Lines 493-530):
- ✅ Requires superuser (TODO: should allow admins on resource)
- ✅ Returns 404 if assignment not found
- ✅ Cascading delete via database constraints

### Database Model

**File:** `python_apps/auth_api/app/db/models_rbac.py`

```python
class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"
    
    user_id: Mapped[int]  # FK to users.id
    resource_id: Mapped[uuid.UUID]  # FK to org/account/project
    role: Mapped[str]  # superadmin, admin, editor, viewer
    resource_type: Mapped[str]  # organization, account, project
    created_at: Mapped[datetime]
    
    # Composite primary key: (user_id, resource_id)
    # Check constraints enforce valid roles and resource types
```

### Schemas

**File:** `python_apps/auth_api/app/schemas/rbac.py`

```python
class UserRoleAssignmentCreate(BaseModel):
    user_id: int
    role: RoleType  # Enum: superadmin, admin, editor, viewer
    resource_type: ResourceType  # Enum: organization, account, project
    resource_id: UUID

class UserRoleAssignmentResponse(BaseModel):
    user_id: int
    resource_id: UUID
    role: str
    resource_type: str
    created_at: datetime
```

## 2. ❌ Permission Overrides (NOT IMPLEMENTED in Auth API)

### Current Status

Permission overrides are **NOT implemented** in the Auth API. However, they **DO exist** in the legacy RBAC service at `python_apps/rbac`.

### Legacy RBAC Service Implementation

**File:** `python_apps/rbac/rbac_api/app/routes/user.py`

The legacy service has these endpoints:

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/users/{user_id}/projects/{project_id}/permission-overrides` | PATCH | ⚠️ Legacy | Update project permission overrides |
| `/users/{user_id}/projects/{project_id}/permission-overrides` | GET | ⚠️ Legacy | Get project permission overrides |

**Implementation Details** (Lines 555-697):
- Uses JSONB field for storing overrides
- Format: `{"Allow": [...actions...], "Deny": [...actions...]}`
- Requires admin permissions
- Cannot override permissions for superadmin/account-admin/project-admin users
- Project-scoped only (no account or organization overrides)

### Legacy Database Model

**File:** `python_packages/elevaitedblib/elevaitelib/orm/db/models.py`

```python
class User_Project(Base):
    __tablename__ = "user_project"
    
    id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    project_id: Mapped[uuid.UUID]
    permission_overrides: Mapped[dict[str, Any]]  # JSONB column
```

### What Needs to Be Done

To implement permission overrides in Auth API:

1. **Add database model** (or reuse existing `User_Project` table)
2. **Create Pydantic schemas** for override requests/responses
3. **Implement endpoints**:
   - `POST /api/rbac/permission_overrides` - Create/update overrides
   - `GET /api/rbac/permission_overrides` - List overrides
   - `DELETE /api/rbac/permission_overrides/{user_id}/{project_id}` - Delete overrides
4. **Update OPA policy** to check overrides (see Section 3)

## 3. ⚠️ OPA Policy - NO Override Support

### Current Policy

**File:** `python_apps/auth_api/policies/rbac.rego`

The current OPA policy (55 lines) does **NOT** support permission overrides. It only checks:
1. User has a role assignment
2. Role assignment matches the resource hierarchy
3. Role has permission for the action

### Policy Logic

```rego
allow if {
    some assignment in input.user.assignments
    valid_resource_match(assignment)  # Check hierarchy
    role_check(assignment)  # Check role permissions
}
```

**Supported Roles:**
- `superadmin` - Full access to organization and below
- `admin` - Full access to account and its projects
- `editor` - Edit and view project
- `viewer` - View project only

### What's Missing

The policy does **NOT** check for:
- ❌ Permission overrides (Allow/Deny lists)
- ❌ User-specific exceptions to role permissions
- ❌ Project-level permission customization

### Required Changes

To support overrides, the policy needs to:

1. **Accept overrides in input**:
```rego
# Current input structure:
{
    "user": {
        "status": "active",
        "assignments": [...]
    },
    "action": "edit_project",
    "resource": {...}
}

# New input structure (add overrides):
{
    "user": {
        "status": "active",
        "assignments": [...],
        "overrides": {  # NEW
            "project_id": {
                "allow": ["edit_project"],
                "deny": ["delete_project"]
            }
        }
    },
    "action": "edit_project",
    "resource": {...}
}
```

2. **Add override logic**:
```rego
# Check explicit deny first (deny takes precedence)
deny if {
    some override in input.user.overrides
    override.resource_id == input.resource.id
    input.action in override.deny
}

# Check explicit allow
allow if {
    some override in input.user.overrides
    override.resource_id == input.resource.id
    input.action in override.allow
}

# Fall back to role-based permissions
allow if {
    not deny
    some assignment in input.user.assignments
    valid_resource_match(assignment)
    role_check(assignment)
}
```

## 4. ✅ Authorization Endpoint (COMPLETE)

### Endpoint

**File:** `python_apps/auth_api/app/routers/authz.py`

`POST /api/authz/check_access` - Fully functional

**Features:**
- ✅ Validates user exists
- ✅ Checks user status is 'active'
- ✅ Retrieves user's role assignments
- ✅ Calls OPA to evaluate policy
- ✅ Returns allowed/denied with reason
- ✅ Fail-closed security (errors = deny)

**Current Flow:**
1. Validate user exists and is active
2. Fetch user's role assignments from database
3. Call OPA with user assignments, action, and resource
4. Return OPA decision

**What Needs to Change:**
- Fetch user's permission overrides from database
- Pass overrides to OPA in the input payload
- Update OPA policy to honor overrides

## 5. ✅ Resource Management Endpoints (COMPLETE)

All resource CRUD endpoints are fully implemented:

### Organizations
- ✅ `POST /api/rbac/organizations` - Create
- ✅ `GET /api/rbac/organizations` - List
- ✅ `GET /api/rbac/organizations/{id}` - Get

### Accounts
- ✅ `POST /api/rbac/accounts` - Create
- ✅ `GET /api/rbac/accounts` - List
- ✅ `GET /api/rbac/accounts/{id}` - Get

### Projects
- ✅ `POST /api/rbac/projects` - Create
- ✅ `GET /api/rbac/projects` - List
- ✅ `GET /api/rbac/projects/{id}` - Get

## 6. Summary & Recommendations

### What's Complete ✅

1. **Role Assignment System** - Fully functional CRUD operations
2. **Resource Hierarchy** - Organizations → Accounts → Projects
3. **Authorization Endpoint** - Working with role-based permissions
4. **OPA Integration** - Policy evaluation working
5. **Database Models** - All tables created and working
6. **RBAC SDK** - Production-ready with 318 tests, 98% coverage

### What's Missing ❌

1. **Permission Overrides API** - Not implemented in Auth API
2. **OPA Override Support** - Policy doesn't check overrides
3. **Override Database Integration** - Auth API doesn't fetch/store overrides

### Recommended Implementation Order

**Phase 1: Database & Models** (2-3 hours)
1. Add `permission_overrides` table (or reuse `user_project`)
2. Create Pydantic schemas for overrides
3. Add database migration

**Phase 2: API Endpoints** (3-4 hours)
1. Implement `POST /api/rbac/permission_overrides`
2. Implement `GET /api/rbac/permission_overrides`
3. Implement `DELETE /api/rbac/permission_overrides/{user_id}/{project_id}`
4. Add validation and authorization

**Phase 3: OPA Policy** (2-3 hours)
1. Update `rbac.rego` to accept overrides in input
2. Add deny-first logic (explicit deny takes precedence)
3. Add allow logic (explicit allow grants access)
4. Test with various override scenarios

**Phase 4: Integration** (2-3 hours)
1. Update `/api/authz/check_access` to fetch overrides
2. Pass overrides to OPA in input payload
3. Add integration tests

**Phase 5: Testing** (3-4 hours)
1. Unit tests for override endpoints
2. Integration tests with OPA
3. End-to-end tests with RBAC SDK

**Total Estimated Time:** 12-17 hours

### Notes

- The legacy RBAC service (`python_apps/rbac`) has a working implementation that can be used as reference
- Permission overrides should follow the same pattern: `{"allow": [...], "deny": [...]}`
- Deny should take precedence over allow (security best practice)
- Consider whether overrides should be project-scoped only or support account/org levels

