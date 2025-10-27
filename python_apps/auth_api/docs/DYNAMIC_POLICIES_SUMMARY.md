# Dynamic Policy Management - Summary

**YES! You can update rego policies via API without redeploying!** 🎉

---

## 🎯 What I Built

### New API Endpoints

All endpoints require **superuser** authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/policies/generate` | POST | Generate policy for a service |
| `/api/policies/upload` | POST | Upload custom rego code |
| `/api/policies` | GET | List all policies |
| `/api/policies/{module}` | GET | Get specific policy |
| `/api/policies/{module}` | DELETE | Delete a policy |

### New Files Created

1. **`app/services/policy_service.py`** - OPA policy management service
2. **`app/routers/policies.py`** - Policy management API endpoints
3. **`DYNAMIC_POLICY_MANAGEMENT.md`** - Complete guide
4. **`examples/test_dynamic_policies.sh`** - Bash test script
5. **`examples/dynamic_policy_example.py`** - Python example

### Updated Files

- **`app/main.py`** - Registered policies router

---

## 🚀 How It Works

### Architecture

```
┌─────────────────────────────────────────┐
│         Admin UI / API Call             │
│  "Add workflow permissions"             │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Auth API - Policy Management       │
│      POST /api/policies/generate        │
│  - Generates rego code                  │
│  - Validates syntax                     │
│  - Uploads to OPA                       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         OPA Policy API                  │
│    PUT /v1/policies/rbac/workflows      │
│  - Stores policy in memory              │
│  - Takes effect immediately             │
│  - No restart needed!                   │
└─────────────────────────────────────────┘
```

### Policy Modules

OPA supports multiple policy modules, all loaded together:

```
OPA Memory:
├── rbac/core              (Base rules - user status, superadmin)
├── rbac/workflow_engine   (Workflow permissions)
├── rbac/agent_studio      (Agent permissions)
├── rbac/reports           (Report permissions)
└── rbac/custom_analyst    (Custom rules)
```

All modules are evaluated together when checking access!

---

## 📝 Usage Examples

### Example 1: Add Workflow Service (Simple)

```bash
curl -X POST http://localhost:8004/auth-api/api/policies/generate \
  -H "Authorization: Bearer <superuser-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "belongs_to": "project",
    "actions": {
      "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow"],
      "editor": ["create_workflow", "edit_workflow", "view_workflow"],
      "viewer": ["view_workflow"]
    }
  }'
```

**Response:**
```json
{
  "message": "Policy for workflow_engine created successfully",
  "module_name": "rbac/workflow_engine",
  "rego_code": "package rbac\n\nimport rego.v1\n\n..."
}
```

**That's it!** The policy is now active. No restart needed.

### Example 2: Upload Custom Rego

```bash
curl -X POST http://localhost:8004/auth-api/api/policies/upload \
  -H "Authorization: Bearer <superuser-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "rbac/custom_rules",
    "rego_code": "package rbac\n\nimport rego.v1\n\nrole_check(assignment) if {\n  assignment.role == \"analyst\"\n  input.action == \"export_data\"\n}"
  }'
```

### Example 3: List All Policies

```bash
curl http://localhost:8004/auth-api/api/policies \
  -H "Authorization: Bearer <superuser-token>"
```

**Response:**
```json
[
  {"id": "rbac/core", "name": "rbac/core"},
  {"id": "rbac/workflow_engine", "name": "rbac/workflow_engine"},
  {"id": "rbac/agent_studio", "name": "rbac/agent_studio"}
]
```

---

## 🎨 Admin UI Workflow

Here's how an admin would use this:

### Scenario: Add New "Reports" Service

**Step 1: Admin opens UI**
```
┌─────────────────────────────────────┐
│  Policy Management                  │
├─────────────────────────────────────┤
│  [Add New Service]                  │
│                                     │
│  Service Name: reports              │
│  Resource Type: report              │
│  Belongs To: [project ▼]            │
│                                     │
│  Permissions:                       │
│  ☑ Admin: create, edit, view, delete│
│  ☑ Editor: create, edit, view       │
│  ☑ Viewer: view                     │
│                                     │
│  [Generate Policy] [Cancel]         │
└─────────────────────────────────────┘
```

**Step 2: UI calls API**
```javascript
await fetch('/api/policies/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    service_name: 'reports',
    resource_type: 'report',
    belongs_to: 'project',
    actions: {
      admin: ['create_report', 'edit_report', 'view_report', 'delete_report'],
      editor: ['create_report', 'edit_report', 'view_report'],
      viewer: ['view_report']
    }
  })
});
```

**Step 3: Policy is live!**
```
✅ Policy created successfully!
   Module: rbac/reports
   
   Users can now access reports based on their roles.
   No deployment needed - changes are live immediately.
```

---

## 🔒 Security Features

### 1. Superuser Only

All policy endpoints require superuser authentication:

```python
@router.post("/policies/generate")
async def generate_service_policy(
    data: ServicePolicyCreate,
    current_user = Depends(require_superuser),  # ← Only superusers!
    ...
):
```

### 2. Syntax Validation

Rego code is validated before uploading:

```python
# Validate syntax
is_valid, error_msg = await policy_service.validate_rego_syntax(rego_code)
if not is_valid:
    raise HTTPException(status_code=400, detail=f"Invalid rego syntax: {error_msg}")
```

### 3. Audit Logging

All policy changes are logged:

```python
logger.info(f"User {current_user.id} uploading custom policy: {data.module_name}")
```

**Future enhancement:** Store in database for full audit trail.

---

## 💾 Future Enhancements

### 1. Database-Backed Policies

Store policy rules in PostgreSQL:

```sql
CREATE TABLE policy_rules (
    id UUID PRIMARY KEY,
    service_name VARCHAR(100),
    resource_type VARCHAR(100),
    role VARCHAR(50),
    action VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

Then generate rego from database on startup or on-demand.

### 2. Policy Versioning

```sql
CREATE TABLE policy_versions (
    id UUID PRIMARY KEY,
    module_name VARCHAR(200),
    version INTEGER,
    rego_code TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

Allow rollback to previous versions.

### 3. Policy Testing UI

```
┌─────────────────────────────────────┐
│  Test Policy                        │
├─────────────────────────────────────┤
│  User ID: 123                       │
│  Role: editor                       │
│  Action: edit_workflow              │
│  Resource: workflow-456             │
│                                     │
│  [Test Access]                      │
│                                     │
│  Result: ✅ Allowed                 │
│  Reason: Editor can edit workflows  │
└─────────────────────────────────────┘
```

### 4. Organization-Specific Policies

Allow org admins to customize policies for their org:

```
OPA Policies:
├── rbac/core                    (Global)
├── rbac/workflow_engine         (Global)
├── rbac/org_123/custom_rules    (Org-specific)
└── rbac/org_456/custom_rules    (Org-specific)
```

---

## 🎯 Key Benefits

### ✅ No Redeployment

- Update policies via API
- Changes take effect immediately
- No container restart needed

### ✅ Per-Service Policies

- Each service has its own policy module
- Easy to manage and understand
- Can update one service without affecting others

### ✅ Admin-Friendly

- Generate policies from simple JSON
- No need to write rego code
- Validate syntax automatically

### ✅ Flexible

- Can generate standard CRUD policies
- Can upload custom rego for advanced use cases
- Can mix both approaches

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `DYNAMIC_POLICIES_SUMMARY.md` | This file - quick overview |
| `DYNAMIC_POLICY_MANAGEMENT.md` | Complete guide with all options |
| `OPA_POLICY_GUIDE.md` | How to write rego policies |
| `examples/test_dynamic_policies.sh` | Bash test script |
| `examples/dynamic_policy_example.py` | Python example |
| `examples/add_workflow_service.md` | Step-by-step workflow example |

---

## 🚀 Next Steps

### Immediate

1. ✅ **Test the API** - Use the example scripts
2. ✅ **Add your first service** - Try workflow or agent service
3. ✅ **Verify it works** - Test authorization with new policies

### Short-term

1. **Build Admin UI** - Policy management interface
2. **Add to database** - Store policy metadata
3. **Add audit logging** - Track all policy changes

### Long-term

1. **Policy versioning** - Rollback capability
2. **Policy testing UI** - Test before deploying
3. **Org-specific policies** - Per-organization customization
4. **Policy templates** - Common patterns library

---

## 🎊 Summary

**You asked:** "Is there any way we could update the rego through the API?"

**Answer:** YES! ✅

**What you can do now:**

1. ✅ Add new services via API (no deployment)
2. ✅ Update permissions via API (no deployment)
3. ✅ Upload custom rego via API (no deployment)
4. ✅ Have separate policy files per service
5. ✅ Build admin UI for policy management

**All changes take effect immediately!** 🚀

The implementation is ready to use. Just start Auth API and try the examples!

