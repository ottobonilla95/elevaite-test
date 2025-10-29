# Admin Guide: Managing User Permissions

This guide explains how administrators can manage user permissions in the Workflow Engine PoC using the Auth API.

## Table of Contents

1. [Overview](#overview)
2. [Permission Model](#permission-model)
3. [Getting Started](#getting-started)
4. [Managing Permissions](#managing-permissions)
5. [Common Scenarios](#common-scenarios)
6. [Testing Permissions](#testing-permissions)
7. [Troubleshooting](#troubleshooting)

## Overview

The Workflow Engine PoC uses a hierarchical Role-Based Access Control (RBAC) system with three levels:

- **Organization** - Top-level entity (e.g., your company)
- **Account** - Department or team within an organization
- **Project** - Specific project or workspace within an account

Users are assigned roles at different levels, which determine their permissions.

### Important Distinction

**This guide covers how admins assign roles to users.** The permissions for each role (what actions a role can perform) are defined in the OPA policy file, not through the API.

- **Role Assignments** (This Guide) - Admins assign roles to users via Auth API
- **Role Permissions** (See [ROLE_PERMISSIONS.md](ROLE_PERMISSIONS.md)) - Developers define what each role can do in the OPA policy

**As an admin, you control WHO has WHICH role. Developers control WHAT each role can DO.**

## Permission Model

### Roles

| Role | Level | Permissions |
|------|-------|-------------|
| **Superadmin** | Organization | Full access to everything in the organization |
| **Admin** | Account | Full access to all projects in the account |
| **Editor** | Project | Can create, edit, delete, and execute workflows in the project |
| **Viewer** | Project | Can only view workflows and results in the project |

### Actions

The system uses two main actions:

- **`view_project`** - Read-only access (GET endpoints)
  - Allowed for: Viewer, Editor, Admin, Superadmin
  
- **`edit_project`** - Create, update, delete, execute (POST, PUT, PATCH, DELETE endpoints)
  - Allowed for: Editor, Admin, Superadmin

### Permission Hierarchy

Permissions flow down the hierarchy:

```
Organization (Superadmin)
  ├── Has full access to all accounts and projects
  │
  └── Account (Admin)
      ├── Has full access to all projects in this account
      │
      └── Project (Editor/Viewer)
          └── Has access only to this specific project
```

## Getting Started

### Prerequisites

1. **Admin Access** - You need to be logged in as a superuser or admin
2. **Auth API Running** - The Auth API must be accessible (default: `http://localhost:8004`)
3. **Tools** - `curl` and `jq` for command-line operations

### Step 1: Login as Admin

```bash
# Login to get access token
curl -X POST http://localhost:8004/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@elevaite.com",
    "password": "admin123"
  }' | jq .

# Save the access token
export ADMIN_TOKEN="<access_token_from_response>"
```

### Step 2: Get Resource IDs

You'll need the UUIDs for organizations, accounts, and projects:

```bash
# List organizations
curl -X GET http://localhost:8004/api/rbac/organizations \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

# List accounts
curl -X GET http://localhost:8004/api/rbac/accounts \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

# List projects
curl -X GET http://localhost:8004/api/rbac/projects \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

# Save the IDs you need
export ORG_ID="<organization-uuid>"
export ACCOUNT_ID="<account-uuid>"
export PROJECT_ID="<project-uuid>"
```

## Managing Permissions

### Create Role Assignment

Assign a role to a user:

```bash
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "'$PROJECT_ID'"
  }' | jq .
```

**Parameters:**
- `user_id` - The user's ID (integer, not UUID)
- `role` - One of: `viewer`, `editor`, `admin`, `superadmin`
- `resource_type` - One of: `project`, `account`, `organization`
- `resource_id` - UUID of the resource

**Important:** If an assignment already exists for this user and resource, it will be updated with the new role.

### List Role Assignments

View all role assignments for a user:

```bash
curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?user_id=123" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
```

Filter by resource:

```bash
# By resource ID
curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?resource_id=$PROJECT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

# By resource type
curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?resource_type=project" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
```

### Update Role Assignment

To change a user's role, simply create a new assignment with the same user_id and resource_id:

```bash
# Promote viewer to editor
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "'$PROJECT_ID'"
  }' | jq .
```

### Delete Role Assignment

Remove a user's access:

```bash
curl -X DELETE "http://localhost:8004/api/rbac/user_role_assignments/123/$PROJECT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Note:** Replace `123` with the user ID and `$PROJECT_ID` with the resource UUID.

### Check Authorization

Verify if a user has permission for a specific action:

```bash
curl -X POST http://localhost:8004/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "action": "edit_project",
    "resource": {
      "type": "project",
      "id": "'$PROJECT_ID'",
      "account_id": "'$ACCOUNT_ID'",
      "organization_id": "'$ORG_ID'"
    }
  }' | jq .
```

Response:
```json
{
  "allowed": true,
  "reason": "User has editor role on project"
}
```

## Common Scenarios

### Scenario 1: Onboard a New Team Member

**Goal:** Give a new user editor access to a project

```bash
# 1. Get the user's ID (they should have registered already)
curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?user_id=123" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .

# 2. Assign editor role
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "'$PROJECT_ID'"
  }' | jq .

# 3. Verify the assignment
curl -X POST http://localhost:8004/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "action": "edit_project",
    "resource": {
      "type": "project",
      "id": "'$PROJECT_ID'",
      "account_id": "'$ACCOUNT_ID'",
      "organization_id": "'$ORG_ID'"
    }
  }' | jq .
```

### Scenario 2: Promote a User to Admin

**Goal:** Give a user admin access to an entire account

```bash
# Assign admin role at account level
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role": "admin",
    "resource_type": "account",
    "resource_id": "'$ACCOUNT_ID'"
  }' | jq .
```

**Note:** Admins at account level automatically have access to all projects in that account.

### Scenario 3: Temporary Read-Only Access

**Goal:** Give a contractor temporary viewer access

```bash
# 1. Assign viewer role
curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 456,
    "role": "viewer",
    "resource_type": "project",
    "resource_id": "'$PROJECT_ID'"
  }' | jq .

# 2. When contract ends, revoke access
curl -X DELETE "http://localhost:8004/api/rbac/user_role_assignments/456/$PROJECT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Scenario 4: Audit User Permissions

**Goal:** Review all permissions for a user

```bash
# Get all role assignments for user
curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?user_id=123" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.assignments[] | {role, resource_type, resource_id}'
```

### Scenario 5: Bulk Permission Changes

**Goal:** Change multiple users' roles

```bash
# Create a script to update multiple users
for USER_ID in 101 102 103 104; do
  echo "Updating user $USER_ID..."
  curl -X POST http://localhost:8004/api/rbac/user_role_assignments \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "user_id": '$USER_ID',
      "role": "editor",
      "resource_type": "project",
      "resource_id": "'$PROJECT_ID'"
    }' | jq -r '.role + " assigned to user " + (.user_id | tostring)'
done
```

## Testing Permissions

### Test with API Key

After assigning permissions, test them with the Workflow Engine:

```bash
# 1. User logs in
curl -X POST http://localhost:8004/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }' | jq .

export USER_TOKEN="<access_token>"

# 2. User creates API key
curl -X POST http://localhost:8004/api/auth/api-keys \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My API Key",
    "expires_in_days": 30
  }' | jq .

export API_KEY="<api_key>"

# 3. Test workflow access
curl -X GET http://localhost:8006/workflows/ \
  -H "X-elevAIte-apikey: $API_KEY" \
  -H "X-elevAIte-ProjectId: $PROJECT_ID" \
  -H "X-elevAIte-AccountId: $ACCOUNT_ID" \
  -H "X-elevAIte-OrganizationId: $ORG_ID" | jq .
```

### Run Automated Tests

```bash
cd python_apps/workflow-engine-poc

# Run RBAC E2E tests
pytest tests/test_rbac_e2e.py -v

# Run permission management demo script
export ADMIN_EMAIL=admin@elevaite.com
export ADMIN_PASSWORD=admin123
./examples/rbac_permission_management.sh
```

## Troubleshooting

### Issue: "Only superusers can assign roles"

**Cause:** Your user account doesn't have superuser privileges.

**Solution:**
```sql
-- Update user to be superuser (run in database)
UPDATE users SET is_superuser = true WHERE email = 'your-email@example.com';
```

### Issue: "User CANNOT view/edit project"

**Possible causes:**

1. **User status is not ACTIVE**
   ```bash
   # Check user status
   SELECT id, email, status FROM users WHERE id = 123;
   
   # Update if needed
   UPDATE users SET status = 'active' WHERE id = 123;
   ```

2. **Role assignment doesn't exist**
   ```bash
   # Check assignments
   curl -X GET "http://localhost:8004/api/rbac/user_role_assignments?user_id=123" \
     -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
   ```

3. **OPA is not running**
   ```bash
   # Check OPA health
   curl http://localhost:8181/health
   ```

### Issue: "Failed to list workflows"

**Possible causes:**

1. **Missing required headers**
   - Ensure all headers are present: `X-elevAIte-apikey`, `X-elevAIte-ProjectId`, `X-elevAIte-AccountId`, `X-elevAIte-OrganizationId`

2. **Invalid API key**
   - API key may be expired or invalid
   - Create a new API key

3. **Workflow Engine not running**
   ```bash
   curl http://localhost:8006/health
   ```

### Debug Mode

Enable verbose output to see what's happening:

```bash
# Add -v flag to curl
curl -v -X GET http://localhost:8004/api/rbac/user_role_assignments?user_id=123 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Additional Resources

- [ROLE_PERMISSIONS.md](ROLE_PERMISSIONS.md) - How to modify what each role can access (for developers)
- [RBAC Integration Documentation](RBAC_INTEGRATION.md) - Technical implementation details
- [Examples Directory](examples/README.md) - Example scripts and usage
- [RBAC SDK Documentation](../../python_packages/rbac-sdk/README.md) - SDK reference
- [Auth API Documentation](../auth_api/README.md) - Complete API reference

