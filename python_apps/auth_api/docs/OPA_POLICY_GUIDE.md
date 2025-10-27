# OPA Policy Guide - How to Modify rbac.rego

This guide shows you how to add new services, actions, and permissions to the OPA policy.

---

## 📋 Understanding the Current Policy

### Current Structure

The policy file (`policies/rbac.rego`) defines:

1. **Roles:** superadmin, admin, editor, viewer
2. **Resources:** organization, account, project
3. **Actions:** manage_account, edit_project, view_project

### How It Works

When a service calls `/api/authz/check_access`, it sends:

```json
{
  "user_id": 123,
  "action": "view_project",
  "resource": {
    "type": "project",
    "id": "proj-uuid",
    "organization_id": "org-uuid",
    "account_id": "acct-uuid"
  }
}
```

OPA evaluates:
1. ✅ Is user status "active"?
2. ✅ Does user have a role assignment that matches the resource?
3. ✅ Does that role allow the requested action?

---

## 🎯 Common Scenarios

### Scenario 1: Add a New Action to Existing Resource

**Example:** Add "delete_project" action

#### Step 1: Decide Which Roles Can Perform It

- superadmin: ✅ Yes (can do everything)
- admin: ✅ Yes (can manage accounts and projects)
- editor: ❌ No (can only edit, not delete)
- viewer: ❌ No (read-only)

#### Step 2: Update the Policy

Edit `python_apps/auth_api/policies/rbac.rego`:

```rego
# Add to the admin role_check (around line 64-68)
role_check(assignment) if {
    assignment.role == "admin"
    input.resource.type in {"account", "project"}
    input.action in {"manage_account", "edit_project", "view_project", "delete_project"}  # ← Added!
}
```

#### Step 3: Reload OPA

```bash
# In Docker Compose, just restart OPA
docker compose -f docker-compose.prod.yaml restart opa

# OPA automatically reloads the policy file
```

#### Step 4: Test It

```bash
curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "delete_project",
    "resource": {
      "type": "project",
      "id": "proj-uuid",
      "organization_id": "org-uuid",
      "account_id": "acct-uuid"
    }
  }'
```

---

### Scenario 2: Add a New Resource Type

**Example:** Add "workflow" resource that belongs to projects

#### Step 1: Define the Hierarchy

```
Organization
└── Account
    └── Project
        └── Workflow  ← NEW!
```

#### Step 2: Update valid_resource_match

Add to `rbac.rego`:

```rego
# Add after the existing valid_resource_match rules (around line 58)

# Workflows belong to projects, so check project-level permissions
valid_resource_match(assignment) if {
    assignment.resource_type == "project"
    input.resource.type == "workflow"
    input.resource.project_id == assignment.resource_id
}
```

#### Step 3: Add Actions for Workflows

```rego
# Add new role_check rules for workflows

role_check(assignment) if {
    assignment.role == "admin"
    input.resource.type == "workflow"
    input.action in {"create_workflow", "edit_workflow", "view_workflow", "delete_workflow"}
}

role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "workflow"
    input.action in {"create_workflow", "edit_workflow", "view_workflow"}
}

role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "workflow"
    input.action == "view_workflow"
}
```

#### Step 4: Update Your Service

When calling check_access, include the project_id:

```python
from rbac_sdk import check_access

allowed = check_access(
    user_id=123,
    action="edit_workflow",
    resource={
        "type": "workflow",
        "id": "workflow-uuid",
        "project_id": "proj-uuid",      # ← Links to project
        "account_id": "acct-uuid",
        "organization_id": "org-uuid"
    }
)
```

---

### Scenario 3: Protect a New Service/API

**Example:** You have a "Reports API" that needs authorization

#### Step 1: Decide Resource Model

Option A: Reports belong to projects (recommended)
```
Project → Reports
```

Option B: Reports are standalone resources
```
Organization → Reports
```

Let's use **Option A** (reports belong to projects):

#### Step 2: Add Report Actions to Policy

```rego
# Add to rbac.rego

# Admins can do everything with reports
role_check(assignment) if {
    assignment.role == "admin"
    input.resource.type == "report"
    input.action in {"create_report", "edit_report", "view_report", "delete_report", "export_report"}
}

# Editors can create, edit, view, export (but not delete)
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "report"
    input.action in {"create_report", "edit_report", "view_report", "export_report"}
}

# Viewers can only view and export
role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "report"
    input.action in {"view_report", "export_report"}
}

# Reports belong to projects, so match project assignments
valid_resource_match(assignment) if {
    assignment.resource_type == "project"
    input.resource.type == "report"
    input.resource.project_id == assignment.resource_id
}
```

#### Step 3: Integrate in Your Reports API

```python
# reports_api/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from rbac_sdk import check_access

app = FastAPI()

@app.get("/reports/{report_id}")
async def get_report(report_id: str, current_user: User = Depends(get_current_user)):
    # Get report from database
    report = get_report_from_db(report_id)
    
    # Check authorization
    allowed = check_access(
        user_id=current_user.id,
        action="view_report",
        resource={
            "type": "report",
            "id": report_id,
            "project_id": report.project_id,
            "account_id": report.account_id,
            "organization_id": report.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return report

@app.post("/reports")
async def create_report(data: ReportCreate, current_user: User = Depends(get_current_user)):
    # Check authorization BEFORE creating
    allowed = check_access(
        user_id=current_user.id,
        action="create_report",
        resource={
            "type": "report",
            "id": "new",  # Not created yet
            "project_id": data.project_id,
            "account_id": data.account_id,
            "organization_id": data.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create the report
    report = create_report_in_db(data)
    return report
```

---

### Scenario 4: Add a Custom Role

**Example:** Add "analyst" role (can view and export, but not edit)

#### Step 1: Update Database

The `user_role_assignments` table has a CHECK constraint. Update the migration:

```sql
-- In a new migration file
ALTER TABLE user_role_assignments 
DROP CONSTRAINT ck_user_role_assignments_role;

ALTER TABLE user_role_assignments 
ADD CONSTRAINT ck_user_role_assignments_role 
CHECK (role IN ('superadmin', 'admin', 'editor', 'viewer', 'analyst'));
```

#### Step 2: Update Pydantic Schema

```python
# app/schemas/rbac.py
class RoleType(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    ANALYST = "analyst"  # ← NEW!
```

#### Step 3: Add to OPA Policy

```rego
# Add to rbac.rego

# Analyst can view and export projects
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "project"
    input.action in {"view_project", "export_project"}
}

# Analyst can view and export reports
role_check(assignment) if {
    assignment.role == "analyst"
    input.resource.type == "report"
    input.action in {"view_report", "export_report"}
}

# Analyst assignments match at project level
valid_resource_match(assignment) if {
    assignment.role == "analyst"
    assignment.resource_type == "project"
    input.resource.id == assignment.resource_id
}
```

---

## 🧪 Testing Your Changes

### Test with OPA CLI

```bash
# Install OPA CLI
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
chmod +x opa

# Test the policy
./opa eval -d policies/rbac.rego \
  -i test_input.json \
  'data.rbac.allow'

# test_input.json:
{
  "user": {
    "id": "123",
    "status": "active",
    "assignments": [
      {
        "role": "editor",
        "resource_type": "project",
        "resource_id": "proj-uuid"
      }
    ]
  },
  "action": "edit_project",
  "resource": {
    "type": "project",
    "id": "proj-uuid",
    "organization_id": "org-uuid",
    "account_id": "acct-uuid"
  }
}
```

### Test via Auth API

```bash
curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "your_new_action",
    "resource": {
      "type": "your_resource_type",
      "id": "resource-uuid",
      "organization_id": "org-uuid",
      "account_id": "acct-uuid"
    }
  }'
```

---

## 📝 Policy Patterns

### Pattern 1: Hierarchical Permissions

Superadmin at org level can access everything below:

```rego
valid_resource_match(assignment) if {
    assignment.role == "superadmin"
    assignment.resource_type == "organization"
    assignment.resource_id == input.resource.organization_id
}
```

### Pattern 2: Resource-Specific Permissions

Admin at account level can access account and its projects:

```rego
valid_resource_match(assignment) if {
    assignment.role == "admin"
    assignment.resource_type == "account"
    assignment.resource_id == input.resource.account_id
}
```

### Pattern 3: Action-Based Permissions

Different roles can perform different actions:

```rego
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "project"
    input.action in {"edit_project", "view_project"}  # Can edit and view
}

role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "project"
    input.action == "view_project"  # Can only view
}
```

---

## 🔄 Deployment Workflow

### 1. Update Policy File

Edit `python_apps/auth_api/policies/rbac.rego`

### 2. Test Locally

```bash
# Test with OPA CLI or via Auth API
opa eval -d policies/rbac.rego -i test_input.json 'data.rbac.allow'
```

### 3. Deploy to Production

**Docker Compose:**
```bash
# Policy file is mounted as volume, so just restart OPA
docker compose -f docker-compose.prod.yaml restart opa
```

**Kubernetes:**
```bash
# Update ConfigMap
kubectl create configmap opa-policy \
  --from-file=rbac.rego=policies/rbac.rego \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart OPA pods to reload
kubectl rollout restart deployment auth-api
```

### 4. Verify

```bash
curl http://localhost:8004/auth-api/api/authz/health
```

---

## 🎯 Best Practices

### 1. Start Restrictive

```rego
# Good: Default deny
default allow := false

# Bad: Default allow
default allow := true
```

### 2. Always Check User Status

```rego
# Good: Check status first
allow if {
    user_is_active
    # ... other checks
}

# Bad: Skip status check
allow if {
    # ... only check permissions
}
```

### 3. Use Descriptive Action Names

```rego
# Good: Clear intent
input.action in {"create_report", "edit_report", "delete_report"}

# Bad: Vague
input.action in {"write", "modify", "remove"}
```

### 4. Document Your Rules

```rego
# Good: Explain the rule
# Editors can create and edit reports, but not delete them
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "report"
    input.action in {"create_report", "edit_report"}
}
```

### 5. Test Edge Cases

- Inactive users
- Users with no assignments
- Users with multiple assignments
- Invalid resource types
- Invalid actions

---

## 🐛 Debugging

### Enable OPA Decision Logs

```yaml
# opa_config.yaml
decision_logs:
  console: true
```

### View OPA Logs

```bash
docker compose -f docker-compose.prod.yaml logs opa
```

### Test Specific Scenarios

```bash
# Test deny reason
./opa eval -d policies/rbac.rego \
  -i test_input.json \
  'data.rbac.deny_reason'
```

---

## 📚 Resources

- [OPA Documentation](https://www.openpolicyagent.org/docs/latest/)
- [Rego Language Reference](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [OPA Playground](https://play.openpolicyagent.org/) - Test policies online

---

## 🎊 Summary

**To add a new service/API:**

1. Decide resource model (belongs to project? account? org?)
2. Add `role_check` rules for each role + action combination
3. Add `valid_resource_match` rule if needed
4. Update your service to call `check_access`
5. Test the policy
6. Deploy (restart OPA)

**The policy file is just a text file** - edit it like any code, test it, and deploy! 🚀

