# Creating New Roles - Complete Guide

How to easily create and manage custom roles in your RBAC system.

---

## ✅ Yes! Creating New Roles is Super Easy!

You can create **unlimited custom roles** with any permissions you want. No database changes needed!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Define the Role in Rego

Add a `role_check` rule to your policy:

```rego
# New "analyst" role
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "project"
    input.action in {"view_project", "export_data", "view_reports"}
}
```

### Step 2: Upload the Policy

```bash
curl -X POST http://localhost:8004/auth-api/api/policies/upload \
  -H "Authorization: Bearer <superuser-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "rbac/analyst_role",
    "rego_code": "package rbac\n\nimport rego.v1\n\nrole_check(assignment) if {\n    assignment.role == \"analyst\"\n    input.resource.type == \"project\"\n    input.action in {\"view_project\", \"export_data\", \"view_reports\"}\n}"
  }'
```

### Step 3: Assign the Role to Users

```bash
curl -X POST http://localhost:8004/auth-api/api/rbac/role-assignments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "role": "analyst",
    "resource_type": "project",
    "resource_id": "project-123"
  }'
```

**Done!** The user can now use the new role immediately! 🎉

---

## 📋 Role Examples

### Example 1: Simple Role (Read-Only Analyst)

```rego
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "project"
    input.action in {"view_project", "export_data", "view_reports"}
}
```

**Permissions:**
- ✅ View projects
- ✅ Export data
- ✅ View reports
- ❌ Cannot edit anything

---

### Example 2: Contributor Role (Create but Not Delete)

```rego
role_check(assignment) if {
    assignment.role == "contributor"
    input.resource.type == "project"
    input.action in {"create_content", "edit_own_content", "view_project"}
}

# Can only edit their own content
role_check(assignment) if {
    assignment.role == "contributor"
    input.resource.type == "content"
    input.action == "edit_content"
    input.resource.owner_id == input.user.id
}
```

**Permissions:**
- ✅ Create content
- ✅ Edit own content
- ✅ View projects
- ❌ Cannot edit others' content
- ❌ Cannot delete

---

### Example 3: Billing Admin (Specialized Role)

```rego
role_check(assignment) if {
    assignment.role == "billing_admin"
    input.resource.type == "account"
    input.action in {
        "view_billing",
        "update_payment_method",
        "view_invoices",
        "download_invoices"
    }
}
```

**Permissions:**
- ✅ Manage billing only
- ❌ Cannot access projects or other resources

---

### Example 4: Developer Role (Multiple Resource Types)

```rego
role_check(assignment) if {
    assignment.role == "developer"
    input.resource.type in {"workflow", "agent"}
    input.action in {
        "create_workflow", "edit_workflow", "view_workflow",
        "create_agent", "edit_agent", "view_agent",
        "execute_workflow", "test_agent"
    }
}
```

**Permissions:**
- ✅ Full access to workflows
- ✅ Full access to agents
- ❌ Cannot access account settings

---

### Example 5: Time-Limited Role

```rego
role_check(assignment) if {
    assignment.role == "temp_contractor"
    input.resource.type == "project"
    input.action in {"view_project", "edit_project"}
    # Check expiry
    assignment.expires_at
    time.now_ns() < time.parse_rfc3339_ns(assignment.expires_at)
}
```

**Assign with expiry:**
```python
POST /api/rbac/role-assignments
{
    "user_id": 1,
    "role": "temp_contractor",
    "resource_type": "project",
    "resource_id": "project-123",
    "metadata": {
        "expires_at": "2025-12-31T23:59:59Z"
    }
}
```

---

## 🛠️ Two Ways to Add Roles

### Method 1: Add to Base Policy (Permanent Roles)

**Best for:** Core roles used across your application

1. Edit `policies/rbac.rego`
2. Add your `role_check` rules
3. Restart OPA (if using file-based config) or re-upload policy

**Example:**
```rego
# Add to policies/rbac.rego
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "project"
    input.action in {"view_project", "export_data"}
}
```

---

### Method 2: Upload as Separate Policy Module (Dynamic)

**Best for:** Custom roles, experiments, service-specific roles

1. Write Rego in a separate file
2. Upload via Policy Management API
3. No restart needed!

**Example:**
```bash
# Create the policy
cat > analyst_role.rego << 'EOF'
package rbac

import rego.v1

role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "project"
    input.action in {"view_project", "export_data", "view_reports"}
}
EOF

# Upload it
curl -X POST http://localhost:8004/auth-api/api/policies/upload \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"module_name\": \"rbac/analyst_role\", \"rego_code\": \"$(cat analyst_role.rego | jq -Rs .)\"}"
```

---

## 📊 Role Design Patterns

### Pattern 1: Simple Permission Set

```rego
role_check(assignment) if {
    assignment.role == "role_name"
    input.resource.type == "resource_type"
    input.action in {"action1", "action2", "action3"}
}
```

### Pattern 2: Multiple Resource Types

```rego
role_check(assignment) if {
    assignment.role == "role_name"
    input.resource.type in {"type1", "type2"}
    input.action in {"action1", "action2"}
}
```

### Pattern 3: Conditional Permissions

```rego
role_check(assignment) if {
    assignment.role == "role_name"
    input.resource.type == "resource_type"
    input.action in {"action1", "action2"}
    # Additional condition
    input.user.department == input.resource.department
}
```

### Pattern 4: Hierarchical (Inherits from Another)

```rego
# Senior role has all junior permissions plus more
role_check(assignment) if {
    assignment.role == "senior_developer"
    input.resource.type == "workflow"
    input.action in {
        # All developer actions
        "create_workflow", "edit_workflow", "view_workflow",
        # Plus senior-only actions
        "deploy_to_production", "manage_api_keys"
    }
}
```

### Pattern 5: Owner-Based

```rego
role_check(assignment) if {
    assignment.role == "contributor"
    input.resource.type == "content"
    input.action == "edit_content"
    # Can only edit own content
    input.resource.owner_id == input.user.id
}
```

---

## 🎯 Common Role Templates

### Read-Only Role
```rego
role_check(assignment) if {
    assignment.role == "readonly"
    input.resource.type == "project"
    input.action in {"view_project", "view_data"}
}
```

### Full Access Role
```rego
role_check(assignment) if {
    assignment.role == "full_access"
    input.resource.type == "project"
    # Allow all actions
}
```

### Service-Specific Role
```rego
role_check(assignment) if {
    assignment.role == "workflow_user"
    input.resource.type == "workflow"
    input.action in {"view_workflow", "execute_workflow"}
}
```

---

## 💡 Best Practices

### 1. **Use Descriptive Role Names**
- ✅ Good: `billing_admin`, `workflow_developer`, `data_analyst`
- ❌ Bad: `role1`, `custom`, `temp`

### 2. **Follow Principle of Least Privilege**
```rego
# Give only necessary permissions
role_check(assignment) if {
    assignment.role == "analyst"
    input.action in {"view_project", "export_data"}  # Only what's needed
}
```

### 3. **Document Your Roles**
```rego
# ----------------------------------------------------------------------------
# ANALYST ROLE
# Purpose: Read-only access for data analysis
# Permissions: View projects, export data, view reports
# Used by: Data team members
# ----------------------------------------------------------------------------
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "project"
    input.action in {"view_project", "export_data", "view_reports"}
}
```

### 4. **Group Related Permissions**
```rego
# Define permission sets
view_permissions := {"view_project", "view_data", "view_reports"}
edit_permissions := {"edit_project", "edit_data", "create_content"}

role_check(assignment) if {
    assignment.role == "viewer"
    input.action in view_permissions
}
```

### 5. **Test Your Roles**
```bash
# Test the role
curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Authorization: Bearer <token>" \
  -d '{
    "user_id": 1,
    "action": "export_data",
    "resource": {"type": "project", "id": "project-123"}
  }'
```

---

## 🔧 Complete Example: Adding "Reviewer" Role

### Step 1: Create the Policy

```rego
package rbac

import rego.v1

# ----------------------------------------------------------------------------
# REVIEWER ROLE
# Can view projects and add comments/approvals, but not edit
# ----------------------------------------------------------------------------

role_check(assignment) if {
    assignment.role == "reviewer"
    input.resource.type == "project"
    input.action in {
        "view_project",
        "add_comment",
        "approve",
        "reject",
        "view_history"
    }
}
```

### Step 2: Upload via API

```python
import httpx
import asyncio

async def add_reviewer_role():
    rego_code = """
package rbac

import rego.v1

role_check(assignment) if {
    assignment.role == "reviewer"
    input.resource.type == "project"
    input.action in {"view_project", "add_comment", "approve", "reject"}
}
"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/auth-api/api/policies/upload",
            json={
                "module_name": "rbac/reviewer_role",
                "rego_code": rego_code
            },
            headers={"Authorization": "Bearer <token>"}
        )
        print(f"Role added: {response.status_code}")

asyncio.run(add_reviewer_role())
```

### Step 3: Assign to Users

```python
async def assign_reviewer():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/auth-api/api/rbac/role-assignments",
            json={
                "user_id": 5,
                "role": "reviewer",
                "resource_type": "project",
                "resource_id": "project-123"
            },
            headers={"Authorization": "Bearer <token>"}
        )
        print(f"Role assigned: {response.status_code}")
```

### Step 4: Test

```python
async def test_reviewer():
    async with httpx.AsyncClient() as client:
        # Should allow
        response = await client.post(
            "http://localhost:8004/auth-api/api/authz/check_access",
            json={
                "user_id": 5,
                "action": "add_comment",
                "resource": {
                    "type": "project",
                    "id": "project-123",
                    "organization_id": "org-1",
                    "account_id": "acc-1"
                }
            },
            headers={"Authorization": "Bearer <token>"}
        )
        print(f"Can add comment: {response.json()['allowed']}")  # True
        
        # Should deny
        response = await client.post(
            "http://localhost:8004/auth-api/api/authz/check_access",
            json={
                "user_id": 5,
                "action": "edit_project",
                "resource": {
                    "type": "project",
                    "id": "project-123",
                    "organization_id": "org-1",
                    "account_id": "acc-1"
                }
            },
            headers={"Authorization": "Bearer <token>"}
        )
        print(f"Can edit project: {response.json()['allowed']}")  # False
```

---

## 📚 More Examples

See `examples/custom_roles.rego` for 15+ role examples including:
- Analyst
- Contributor
- Reviewer
- Billing Admin
- Support
- Developer
- Auditor
- Guest
- Owner
- Team Lead
- Data Scientist
- Workflow Manager
- And more!

---

## ✅ Summary

**Creating new roles is easy:**

1. ✅ **No database changes needed**
2. ✅ **Just add Rego rules**
3. ✅ **Upload via API**
4. ✅ **Assign to users**
5. ✅ **Works immediately**

**You can create:**
- ✅ Unlimited custom roles
- ✅ Roles with any permissions
- ✅ Conditional roles
- ✅ Time-limited roles
- ✅ Multi-resource roles
- ✅ Hierarchical roles

**Start now:**
```bash
# View examples
cat python_apps/auth_api/examples/custom_roles.rego

# Create your first custom role!
```

🚀 **It's that simple!**

