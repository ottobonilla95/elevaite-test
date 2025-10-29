# Workflow Engine PoC Examples

This directory contains example scripts and demonstrations for the Workflow Engine PoC.

## RBAC Permission Management

### `rbac_permission_management.sh`

A comprehensive demonstration script showing how admins can manage user permissions through the Auth API.

**What it demonstrates:**

1. **Admin Login** - Authenticate as an admin user
2. **Create User and Grant Viewer Access** - Register a new user and assign viewer role
3. **Promote User from Viewer to Editor** - Update role assignment
4. **List User's Role Assignments** - View all roles assigned to a user
5. **Check Authorization** - Verify user permissions using the authz API
6. **Test with Workflow Engine** - Create API key and test actual workflow access
7. **Revoke Access** - Remove role assignment and verify access is denied

**Prerequisites:**

- Auth API running on `http://localhost:8004` (or set `AUTH_API_URL`)
- Workflow Engine PoC running on `http://localhost:8006` (or set `WORKFLOW_ENGINE_URL`)
- Admin credentials (email and password)
- `jq` installed for JSON parsing

**Usage:**

```bash
# Set admin credentials
export ADMIN_EMAIL=admin@elevaite.com
export ADMIN_PASSWORD=admin123

# Run the script
./examples/rbac_permission_management.sh
```

**Optional environment variables:**

```bash
export AUTH_API_URL=http://localhost:8004        # Auth API URL
export WORKFLOW_ENGINE_URL=http://localhost:8006 # Workflow Engine URL
export ADMIN_EMAIL=admin@elevaite.com            # Admin email
export ADMIN_PASSWORD=admin123                   # Admin password
```

**Expected output:**

The script will:
- Create a new test user with a timestamp-based email
- Assign viewer role to the user
- Promote the user to editor role
- List all role assignments for the user
- Check authorization for view_project and edit_project actions
- Create an API key for the user
- Test workflow listing with the API key
- Revoke the user's access
- Verify access is denied after revocation

**Example output:**

```
========================================
Step 1: Admin Login
========================================

ℹ Logging in as admin to get access token...
✓ Admin logged in successfully (User ID: 1)

========================================
Scenario 1: Create User and Grant Viewer Access
========================================

ℹ Registering new user...
✓ User registered (ID: 123, Email: test-user-1234567890@elevaite.com)
ℹ Getting organization, account, and project IDs...
✓ Org: org-uuid, Account: account-uuid, Project: project-uuid
ℹ Granting viewer access to project...
✓ Viewer role assigned
{
  "user_id": 123,
  "role": "viewer",
  "resource_type": "project",
  "resource_id": "project-uuid",
  ...
}

========================================
Scenario 2: Promote User from Viewer to Editor
========================================

ℹ Updating role assignment to editor...
✓ User promoted to editor
...
```

## Permission Management Workflow

### Understanding the Permission Hierarchy

```
Organization (superadmin)
  └── Account (admin)
      └── Project (editor, viewer)
```

- **Superadmin** at organization level has full access to all accounts and projects
- **Admin** at account level has full access to all projects in that account
- **Editor** at project level can create/edit/delete resources in that project
- **Viewer** at project level can only read resources in that project

### Common Admin Tasks

#### 1. Grant Access to a New Team Member

```bash
# Create role assignment
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "project-uuid"
  }'
```

#### 2. Promote a User

```bash
# Update existing assignment (same endpoint, will update if exists)
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "admin",
    "resource_type": "account",
    "resource_id": "account-uuid"
  }'
```

#### 3. Audit User Permissions

```bash
# List all role assignments for a user
curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?user_id=123" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### 4. Remove Access

```bash
# Delete role assignment
curl -X DELETE http://localhost:8004/api/rbac/user_role_assignments/123/project-uuid \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

#### 5. Verify Permissions

```bash
# Check if user has permission
curl -X POST http://localhost:8004/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "action": "edit_project",
    "resource": {
      "type": "project",
      "id": "project-uuid",
      "account_id": "account-uuid",
      "organization_id": "org-uuid"
    }
  }'
```

## Testing RBAC Integration

### Running E2E Tests

The project includes comprehensive end-to-end tests for RBAC integration:

```bash
cd python_apps/workflow-engine-poc

# Run all RBAC E2E tests
pytest tests/test_rbac_e2e.py -v

# Run specific test
pytest tests/test_rbac_e2e.py::TestWorkflowEndpointsRBAC::test_list_workflows_viewer_allowed -v
```

**Test coverage:**
- 18 E2E tests covering workflows, executions, and agents
- Tests create real users, organizations, accounts, and projects
- Tests verify authorization decisions from OPA
- All tests passing (100%)

### Manual Testing with curl

See the main [RBAC_INTEGRATION.md](../RBAC_INTEGRATION.md) documentation for detailed curl examples.

## Troubleshooting

### Common Issues

**Issue: "Failed to login as admin"**
- Verify Auth API is running: `curl http://localhost:8004/api/health`
- Check admin credentials are correct
- Ensure admin user exists in the database

**Issue: "Only superusers can assign roles"**
- The current user must be a superuser to manage role assignments
- Check user's `is_superuser` flag in the database
- Or use a superuser account

**Issue: "User CANNOT view/edit project"**
- Verify role assignment was created successfully
- Check user status is ACTIVE (not INACTIVE, SUSPENDED, or PENDING)
- Verify OPA is running: `curl http://localhost:8181/health`
- Check OPA policy is loaded correctly

**Issue: "Failed to list workflows"**
- Verify Workflow Engine is running: `curl http://localhost:8006/health`
- Check API key is valid and not expired
- Verify all required headers are present (ProjectId, AccountId, OrganizationId)
- Check user has appropriate role assignment

### Debug Mode

Enable debug logging in the scripts:

```bash
# Add -x flag to see all commands
bash -x ./examples/rbac_permission_management.sh
```

## Additional Resources

- [RBAC Integration Documentation](../RBAC_INTEGRATION.md) - Complete RBAC integration guide
- [RBAC SDK Documentation](../../../python_packages/rbac-sdk/README.md) - RBAC SDK reference
- [Auth API Documentation](../../auth_api/README.md) - Auth API endpoints and schemas
- [OPA Policy](../../auth_api/policies/rbac.rego) - RBAC policy rules

