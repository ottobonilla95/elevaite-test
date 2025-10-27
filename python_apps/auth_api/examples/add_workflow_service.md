# Example: Adding Workflow Service to RBAC

This is a complete, step-by-step example of adding your Workflow Engine to the RBAC system.

---

## 🎯 Goal

Protect the Workflow Engine API with RBAC so that:
- Users can only access workflows in projects they have access to
- Different roles have different permissions (admin can delete, viewer can only view)

---

## 📋 Step 1: Define Permissions

### Resource Model

Workflows belong to projects:
```
Organization
└── Account
    └── Project
        └── Workflow  ← We're adding this
```

### Actions

| Action | Superadmin | Admin | Editor | Viewer |
|--------|-----------|-------|--------|--------|
| `create_workflow` | ✅ | ✅ | ✅ | ❌ |
| `view_workflow` | ✅ | ✅ | ✅ | ✅ |
| `edit_workflow` | ✅ | ✅ | ✅ | ❌ |
| `delete_workflow` | ✅ | ✅ | ❌ | ❌ |
| `execute_workflow` | ✅ | ✅ | ✅ | ❌ |
| `view_execution` | ✅ | ✅ | ✅ | ✅ |

---

## 🔧 Step 2: Update OPA Policy

Edit `python_apps/auth_api/policies/rbac.rego`:

```rego
# Add at the end of the file (after line 81)

# ============================================================================
# Workflow Permissions
# ============================================================================

# Workflows belong to projects, so match project-level assignments
valid_resource_match(assignment) if {
    assignment.resource_type == "project"
    input.resource.type == "workflow"
    input.resource.project_id == assignment.resource_id
}

# Workflow executions also belong to projects (via their workflow)
valid_resource_match(assignment) if {
    assignment.resource_type == "project"
    input.resource.type == "workflow_execution"
    input.resource.project_id == assignment.resource_id
}

# Superadmin can do everything with workflows
role_check(assignment) if {
    assignment.role == "superadmin"
    input.resource.type in {"workflow", "workflow_execution"}
}

# Admin can do everything with workflows
role_check(assignment) if {
    assignment.role == "admin"
    input.resource.type == "workflow"
    input.action in {
        "create_workflow",
        "view_workflow",
        "edit_workflow",
        "delete_workflow",
        "execute_workflow"
    }
}

# Admin can view workflow executions
role_check(assignment) if {
    assignment.role == "admin"
    input.resource.type == "workflow_execution"
    input.action == "view_execution"
}

# Editor can create, view, edit, and execute workflows (but not delete)
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "workflow"
    input.action in {
        "create_workflow",
        "view_workflow",
        "edit_workflow",
        "execute_workflow"
    }
}

# Editor can view workflow executions
role_check(assignment) if {
    assignment.role == "editor"
    input.resource.type == "workflow_execution"
    input.action == "view_execution"
}

# Viewer can only view workflows and executions
role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "workflow"
    input.action == "view_workflow"
}

role_check(assignment) if {
    assignment.role == "viewer"
    input.resource.type == "workflow_execution"
    input.action == "view_execution"
}
```

---

## 🚀 Step 3: Deploy Updated Policy

```bash
# Restart OPA to reload the policy
docker compose -f docker-compose.prod.yaml restart opa

# Verify OPA is healthy
curl http://localhost:8004/auth-api/api/authz/health
```

---

## 💻 Step 4: Integrate in Workflow Engine

### Option A: Using rbac-sdk (Recommended)

```python
# workflow_engine/app/routers/workflows.py
from fastapi import APIRouter, Depends, HTTPException
from rbac_sdk import check_access
from ..dependencies import get_current_user

router = APIRouter()

@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, current_user = Depends(get_current_user)):
    # Get workflow from database
    workflow = await get_workflow_from_db(workflow_id)
    
    # Check authorization
    allowed = check_access(
        user_id=current_user.id,
        action="view_workflow",
        resource={
            "type": "workflow",
            "id": workflow_id,
            "project_id": workflow.project_id,
            "account_id": workflow.account_id,
            "organization_id": workflow.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return workflow


@router.post("/workflows")
async def create_workflow(data: WorkflowCreate, current_user = Depends(get_current_user)):
    # Check authorization BEFORE creating
    allowed = check_access(
        user_id=current_user.id,
        action="create_workflow",
        resource={
            "type": "workflow",
            "id": "new",  # Not created yet
            "project_id": data.project_id,
            "account_id": data.account_id,
            "organization_id": data.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create the workflow
    workflow = await create_workflow_in_db(data)
    return workflow


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    data: WorkflowUpdate,
    current_user = Depends(get_current_user)
):
    workflow = await get_workflow_from_db(workflow_id)
    
    # Check authorization
    allowed = check_access(
        user_id=current_user.id,
        action="edit_workflow",
        resource={
            "type": "workflow",
            "id": workflow_id,
            "project_id": workflow.project_id,
            "account_id": workflow.account_id,
            "organization_id": workflow.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update the workflow
    updated = await update_workflow_in_db(workflow_id, data)
    return updated


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, current_user = Depends(get_current_user)):
    workflow = await get_workflow_from_db(workflow_id)
    
    # Check authorization
    allowed = check_access(
        user_id=current_user.id,
        action="delete_workflow",
        resource={
            "type": "workflow",
            "id": workflow_id,
            "project_id": workflow.project_id,
            "account_id": workflow.account_id,
            "organization_id": workflow.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete the workflow
    await delete_workflow_from_db(workflow_id)
    return {"message": "Workflow deleted"}


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, current_user = Depends(get_current_user)):
    workflow = await get_workflow_from_db(workflow_id)
    
    # Check authorization
    allowed = check_access(
        user_id=current_user.id,
        action="execute_workflow",
        resource={
            "type": "workflow",
            "id": workflow_id,
            "project_id": workflow.project_id,
            "account_id": workflow.account_id,
            "organization_id": workflow.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Execute the workflow
    execution = await execute_workflow_async(workflow_id)
    return execution


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str, current_user = Depends(get_current_user)):
    execution = await get_execution_from_db(execution_id)
    workflow = await get_workflow_from_db(execution.workflow_id)
    
    # Check authorization
    allowed = check_access(
        user_id=current_user.id,
        action="view_execution",
        resource={
            "type": "workflow_execution",
            "id": execution_id,
            "project_id": workflow.project_id,
            "account_id": workflow.account_id,
            "organization_id": workflow.organization_id
        }
    )
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return execution
```

### Option B: Direct HTTP Call

```python
import httpx

async def check_workflow_access(user_id: int, action: str, workflow):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://auth-api:8004/auth-api/api/authz/check_access",
            json={
                "user_id": user_id,
                "action": action,
                "resource": {
                    "type": "workflow",
                    "id": workflow.id,
                    "project_id": workflow.project_id,
                    "account_id": workflow.account_id,
                    "organization_id": workflow.organization_id
                }
            }
        )
        result = response.json()
        return result["allowed"]
```

---

## 🧪 Step 5: Test It

### Test 1: Viewer Can View Workflow

```bash
# Assume user 1 is a viewer on project "proj-123"

curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "view_workflow",
    "resource": {
      "type": "workflow",
      "id": "workflow-456",
      "project_id": "proj-123",
      "account_id": "acct-789",
      "organization_id": "org-001"
    }
  }'

# Expected: {"allowed": true}
```

### Test 2: Viewer Cannot Delete Workflow

```bash
curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "delete_workflow",
    "resource": {
      "type": "workflow",
      "id": "workflow-456",
      "project_id": "proj-123",
      "account_id": "acct-789",
      "organization_id": "org-001"
    }
  }'

# Expected: {"allowed": false, "deny_reason": "insufficient_permissions"}
```

### Test 3: Editor Can Execute Workflow

```bash
# Assume user 2 is an editor on project "proj-123"

curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "action": "execute_workflow",
    "resource": {
      "type": "workflow",
      "id": "workflow-456",
      "project_id": "proj-123",
      "account_id": "acct-789",
      "organization_id": "org-001"
    }
  }'

# Expected: {"allowed": true}
```

### Test 4: Admin Can Delete Workflow

```bash
# Assume user 3 is an admin on account "acct-789"

curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3,
    "action": "delete_workflow",
    "resource": {
      "type": "workflow",
      "id": "workflow-456",
      "project_id": "proj-123",
      "account_id": "acct-789",
      "organization_id": "org-001"
    }
  }'

# Expected: {"allowed": true}
```

---

## 📊 Step 6: Update Workflow Database Schema

Add RBAC fields to your workflow table:

```sql
-- Add to workflow table
ALTER TABLE workflows
ADD COLUMN project_id UUID NOT NULL,
ADD COLUMN account_id UUID NOT NULL,
ADD COLUMN organization_id UUID NOT NULL;

-- Add indexes for performance
CREATE INDEX idx_workflows_project_id ON workflows(project_id);
CREATE INDEX idx_workflows_account_id ON workflows(account_id);
CREATE INDEX idx_workflows_organization_id ON workflows(organization_id);
```

---

## 🎯 Summary

**What we did:**

1. ✅ Defined workflow permissions (who can do what)
2. ✅ Updated OPA policy with workflow rules
3. ✅ Deployed updated policy (restart OPA)
4. ✅ Integrated check_access in Workflow Engine API
5. ✅ Tested all permission scenarios
6. ✅ Updated database schema with RBAC fields

**Now your Workflow Engine is protected!** 🎉

Users can only:
- View workflows in projects they have access to
- Edit/delete based on their role
- Execute workflows if they have editor+ permissions

---

## 🔄 Next Steps

1. Add similar protection to other resources (agents, tools, etc.)
2. Add audit logging for all authorization checks
3. Create admin UI for managing role assignments
4. Add bulk permission checks for list endpoints

---

## 💡 Tips

**For list endpoints:**
```python
@router.get("/workflows")
async def list_workflows(current_user = Depends(get_current_user)):
    # Get user's project assignments from Auth API
    assignments = get_user_assignments(current_user.id)
    
    # Filter workflows to only those in accessible projects
    project_ids = [a.resource_id for a in assignments if a.resource_type == "project"]
    workflows = await get_workflows_by_projects(project_ids)
    
    return workflows
```

**For performance:**
- Cache user assignments (they don't change often)
- Batch authorization checks when possible
- Add database indexes on RBAC fields

