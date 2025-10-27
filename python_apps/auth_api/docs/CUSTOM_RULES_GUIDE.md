# Custom Account/User/Project-Specific Rules Guide

How to implement custom authorization rules for specific accounts, users, or projects.

---

## 🎯 Three Approaches

### 1. Database-Driven Rules (Recommended) ✅

**Best for:** Standard role-based access that changes frequently

**How it works:**
- Users get role assignments stored in the database
- Each assignment is scoped to a specific resource
- No policy changes needed - just manage assignments via API

**Example:**

```python
# Give user "alice" admin access to project-123
POST /api/rbac/role-assignments
{
    "user_id": 1,
    "role": "admin",
    "resource_type": "project",
    "resource_id": "project-123"
}

# Give same user viewer access to project-456
POST /api/rbac/role-assignments
{
    "user_id": 1,
    "role": "viewer",
    "resource_type": "project",
    "resource_id": "project-456"
}
```

**Authorization check:**
```python
# Check if alice can edit project-123
POST /api/authz/check_access
{
    "user_id": 1,
    "action": "edit_project",
    "resource": {
        "type": "project",
        "id": "project-123",
        "organization_id": "org-1",
        "account_id": "acc-1"
    }
}
# Returns: {"allowed": true} ✅
```

**Pros:**
- ✅ No code changes needed
- ✅ Managed via API
- ✅ Dynamic (immediate effect)
- ✅ Scales well
- ✅ Already implemented!

**Cons:**
- ❌ Limited to predefined roles

---

### 2. Custom Policy Rules (For Special Cases)

**Best for:** Complex business logic, special permissions, conditional access

**How it works:**
- Write custom Rego rules
- Upload via Policy Management API
- Rules evaluated alongside standard rules

**Example 1: Project Owner Rule**

```rego
package rbac

import rego.v1

# Only project owners can delete projects
role_check(assignment) if {
    assignment.role == "owner"
    input.resource.type == "project"
    input.action == "delete_project"
    input.resource.id == assignment.resource_id
}
```

**Upload:**
```bash
curl -X POST http://localhost:8004/auth-api/api/policies/upload \
  -H "Authorization: Bearer <superuser-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "rbac/project_owners",
    "rego_code": "<paste rego code here>"
  }'
```

**Example 2: Time-Based Access**

```rego
# Temporary access that expires
role_check(assignment) if {
    assignment.role == "temp_editor"
    input.resource.type == "project"
    input.action in {"edit_project", "view_project"}
    # Check expiry
    time.now_ns() < time.parse_rfc3339_ns(assignment.expires_at)
}
```

**Database schema addition:**
```sql
ALTER TABLE user_role_assignments 
ADD COLUMN expires_at TIMESTAMP NULL;
```

**Example 3: Department-Based Access**

```rego
# Users can only access projects in their department
valid_resource_match(assignment) if {
    assignment.resource_type == "project"
    input.resource.id == assignment.resource_id
    input.user.department == input.resource.department
}
```

**Pros:**
- ✅ Unlimited flexibility
- ✅ Complex business logic
- ✅ Conditional rules
- ✅ Can be updated via API

**Cons:**
- ❌ Requires Rego knowledge
- ❌ More complex to maintain

---

### 3. Hybrid Approach (Best of Both Worlds) 🌟

**Combine database-driven + custom rules**

**Example: Project with custom rules**

```python
# 1. Standard role assignment (database)
POST /api/rbac/role-assignments
{
    "user_id": 1,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "project-123",
    "metadata": {
        "department": "engineering",
        "expires_at": "2025-12-31T23:59:59Z"
    }
}

# 2. Custom policy rule (OPA)
# Upload policy that checks metadata
```

**Custom policy:**
```rego
package rbac

import rego.v1

# Check department match
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "project"
    # Check metadata
    assignment.metadata.department == input.resource.department
    # Check expiry
    time.now_ns() < time.parse_rfc3339_ns(assignment.metadata.expires_at)
}
```

---

## 🚀 Practical Examples

### Example 1: User-Specific Override

**Scenario:** Give user ID 42 special access to a specific project

**Option A: Database (Simple)**
```python
POST /api/rbac/role-assignments
{
    "user_id": 42,
    "role": "admin",
    "resource_type": "project",
    "resource_id": "special-project-123"
}
```

**Option B: Custom Policy (More Control)**
```rego
# Only for user 42 on this specific project
allow if {
    input.user.id == 42
    input.resource.type == "project"
    input.resource.id == "special-project-123"
    input.action in {"view_project", "edit_project"}
}
```

---

### Example 2: Account-Level Rules

**Scenario:** All users in account "acc-premium" get extra permissions

**Custom Policy:**
```rego
# Premium account users get extra features
role_check(assignment) if {
    input.resource.account_id == "acc-premium"
    assignment.role in {"editor", "admin"}
    input.action == "use_premium_features"
}
```

---

### Example 3: Project State-Based Rules

**Scenario:** Archived projects are read-only except for admins

**Custom Policy:**
```rego
# Archived projects are read-only
role_check(assignment) if {
    input.resource.type == "project"
    input.resource.status == "archived"
    assignment.role == "admin"
    # Admins can still edit
}

role_check(assignment) if {
    input.resource.type == "project"
    input.resource.status == "archived"
    assignment.role in {"editor", "viewer"}
    input.action == "view_project"  # Only view
}
```

---

## 📋 Decision Matrix

| Use Case | Approach | Why |
|----------|----------|-----|
| Standard role assignment | Database | Simple, dynamic, no code |
| User X can access Project Y | Database | Just create assignment |
| Time-limited access | Custom Policy + DB | Need expiry logic |
| Department-based access | Custom Policy | Need attribute matching |
| Project owner permissions | Custom Policy | Special role logic |
| Emergency admin access | Custom Policy | Override normal rules |
| Archived project rules | Custom Policy | State-based logic |

---

## 🛠️ Implementation Steps

### For Database-Driven Rules (Recommended Start)

1. **Create role assignment:**
```bash
curl -X POST http://localhost:8004/auth-api/api/rbac/role-assignments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "role": "editor",
    "resource_type": "project",
    "resource_id": "project-123"
  }'
```

2. **Test authorization:**
```bash
curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "edit_project",
    "resource": {
      "type": "project",
      "id": "project-123",
      "organization_id": "org-1",
      "account_id": "acc-1"
    }
  }'
```

### For Custom Policy Rules

1. **Write Rego policy** (see examples above)

2. **Upload policy:**
```bash
curl -X POST http://localhost:8004/auth-api/api/policies/upload \
  -H "Authorization: Bearer <superuser-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "rbac/custom_project_rules",
    "rego_code": "<your rego code>"
  }'
```

3. **Test immediately** (no restart needed!)

---

## 💡 Best Practices

1. **Start with database-driven rules** - Cover 90% of cases
2. **Add custom policies only when needed** - For special logic
3. **Document custom rules** - Explain why they exist
4. **Test thoroughly** - Use `/api/authz/check_access` endpoint
5. **Version control policies** - Keep Rego files in git
6. **Monitor policy performance** - OPA is fast but complex rules can slow down

---

## 📚 Examples in This Repo

- **`examples/custom_project_rules.rego`** - Project-specific rules
- **`policies/rbac.rego`** - Base RBAC rules
- **`examples/add_workflow_service.md`** - Service-specific rules

---

## 🎯 Quick Answer to Your Question

**Yes! You can set up account/user/project-specific rules in two ways:**

1. **Database (Easy):** Create role assignments via API
   ```python
   # User 1 is admin on project-123
   POST /api/rbac/role-assignments
   {"user_id": 1, "role": "admin", "resource_type": "project", "resource_id": "project-123"}
   ```

2. **Custom Policy (Advanced):** Upload Rego rules via API
   ```rego
   # Only user 42 can access special-project
   allow if {
       input.user.id == 42
       input.resource.id == "special-project-123"
   }
   ```

**Both work together!** The system evaluates all rules and grants access if any rule allows it.

---

Need help implementing a specific rule? Let me know the use case! 🚀

