# Dynamic Policy Management - Update Rego via API

This guide shows how to enable dynamic policy updates through an API, allowing admins to modify authorization rules without redeploying.

---

## 🎯 Architecture Options

### Option 1: OPA Policy API (Recommended)

OPA has a built-in REST API for managing policies dynamically.

```
┌─────────────────────────────────────────┐
│         Admin UI / API                  │
│  "Add workflow permissions for editors" │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Auth API - Policy Management       │
│      POST /api/policies/update          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         OPA Policy API                  │
│    PUT /v1/policies/rbac/workflows      │
│    (Updates policy in memory)           │
└─────────────────────────────────────────┘
```

### Option 2: Database-Backed Policies

Store policies in PostgreSQL, generate rego dynamically.

```
┌─────────────────────────────────────────┐
│         Admin UI / API                  │
│  "Add workflow permissions for editors" │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      PostgreSQL - Policy Rules Table    │
│  INSERT INTO policy_rules (...)         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Auth API - Generate Rego           │
│  Convert DB rules → Rego syntax         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         OPA Policy API                  │
│    PUT /v1/policies/rbac/dynamic        │
└─────────────────────────────────────────┘
```

### Option 3: Per-Service Policy Modules

Each service has its own policy module, all loaded into OPA.

```
OPA Policy Structure:
├── rbac/core.rego          (Base rules, user status)
├── rbac/workflows.rego     (Workflow permissions)
├── rbac/agents.rego        (Agent permissions)
├── rbac/reports.rego       (Report permissions)
└── rbac/custom.rego        (Admin-defined rules)
```

---

## 🚀 Implementation: Option 1 (OPA Policy API)

### Step 1: Enable OPA Policy API

Update `python_apps/auth_api/docker-compose.prod.yaml`:

```yaml
opa:
  image: openpolicyagent/opa:0.60.0
  restart: always
  command:
    - "run"
    - "--server"
    - "--addr=0.0.0.0:8181"
    - "--set=decision_logs.console=true"
    # Don't load policies from file, we'll use API
  ports:
    - "8181:8181"  # Expose OPA API (internal only!)
  networks:
    - auth_network
  healthcheck:
    test: ["CMD", "wget", "-O-", "http://localhost:8181/health"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Step 2: Create Policy Management Service

```python
# python_apps/auth_api/app/services/policy_service.py

import httpx
from typing import Dict, List
from app.core.config import settings

class PolicyService:
    """Manage OPA policies dynamically via API"""
    
    def __init__(self):
        self.opa_base_url = settings.OPA_URL.replace("/v1/data/rbac/allow", "")
        self.policy_base_url = f"{self.opa_base_url}/v1/policies"
    
    async def upload_policy(self, module_name: str, rego_code: str) -> bool:
        """Upload or update a policy module in OPA"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.policy_base_url}/{module_name}",
                content=rego_code,
                headers={"Content-Type": "text/plain"}
            )
            return response.status_code == 200
    
    async def get_policy(self, module_name: str) -> str:
        """Get a policy module from OPA"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.policy_base_url}/{module_name}")
            if response.status_code == 200:
                return response.json()["result"]["raw"]
            return None
    
    async def delete_policy(self, module_name: str) -> bool:
        """Delete a policy module from OPA"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.policy_base_url}/{module_name}")
            return response.status_code == 200
    
    async def list_policies(self) -> List[str]:
        """List all policy modules in OPA"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.policy_base_url)
            if response.status_code == 200:
                return list(response.json()["result"].keys())
            return []
    
    async def generate_service_policy(
        self,
        service_name: str,
        resource_type: str,
        actions: Dict[str, List[str]]  # role -> [actions]
    ) -> str:
        """Generate rego policy for a service"""
        
        # Generate valid_resource_match rule
        resource_match = f"""
# {service_name.title()} - Resource matching
valid_resource_match(assignment) if {{
    assignment.resource_type == "project"
    input.resource.type == "{resource_type}"
    input.resource.project_id == assignment.resource_id
}}
"""
        
        # Generate role_check rules for each role
        role_checks = []
        for role, allowed_actions in actions.items():
            actions_str = ", ".join([f'"{a}"' for a in allowed_actions])
            role_checks.append(f"""
# {role.title()} permissions for {resource_type}
role_check(assignment) if {{
    assignment.role == "{role}"
    input.resource.type == "{resource_type}"
    input.action in {{{actions_str}}}
}}""")
        
        # Combine into full policy
        policy = f"""package rbac

import rego.v1

# ============================================================================
# {service_name.upper()} Service Permissions
# Auto-generated policy module
# ============================================================================

{resource_match}

{"".join(role_checks)}
"""
        return policy

# Singleton
_policy_service = None

def get_policy_service() -> PolicyService:
    global _policy_service
    if _policy_service is None:
        _policy_service = PolicyService()
    return _policy_service
```

### Step 3: Create Policy Management API

```python
# python_apps/auth_api/app/routers/policies.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from app.services.policy_service import get_policy_service, PolicyService
from app.dependencies import get_current_user, require_superuser

router = APIRouter()

class ServicePolicyCreate(BaseModel):
    service_name: str
    resource_type: str
    actions: Dict[str, List[str]]  # role -> [actions]
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "workflow_engine",
                "resource_type": "workflow",
                "actions": {
                    "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow"],
                    "editor": ["create_workflow", "edit_workflow", "view_workflow"],
                    "viewer": ["view_workflow"]
                }
            }
        }

class PolicyUpload(BaseModel):
    module_name: str
    rego_code: str

class PolicyResponse(BaseModel):
    module_name: str
    rego_code: str

@router.post("/policies/generate", tags=["policies"])
async def generate_service_policy(
    data: ServicePolicyCreate,
    current_user = Depends(require_superuser),
    policy_service: PolicyService = Depends(get_policy_service)
):
    """
    Generate and upload a policy for a service.
    Only superusers can manage policies.
    """
    # Generate rego code
    rego_code = await policy_service.generate_service_policy(
        service_name=data.service_name,
        resource_type=data.resource_type,
        actions=data.actions
    )
    
    # Upload to OPA
    module_name = f"rbac/{data.service_name}"
    success = await policy_service.upload_policy(module_name, rego_code)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload policy to OPA")
    
    return {
        "message": f"Policy for {data.service_name} created successfully",
        "module_name": module_name,
        "rego_code": rego_code
    }

@router.post("/policies/upload", tags=["policies"])
async def upload_custom_policy(
    data: PolicyUpload,
    current_user = Depends(require_superuser),
    policy_service: PolicyService = Depends(get_policy_service)
):
    """
    Upload a custom rego policy.
    Only superusers can manage policies.
    """
    success = await policy_service.upload_policy(data.module_name, data.rego_code)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload policy to OPA")
    
    return {"message": f"Policy {data.module_name} uploaded successfully"}

@router.get("/policies", tags=["policies"])
async def list_policies(
    current_user = Depends(require_superuser),
    policy_service: PolicyService = Depends(get_policy_service)
):
    """List all policy modules in OPA"""
    policies = await policy_service.list_policies()
    return {"policies": policies}

@router.get("/policies/{module_name}", tags=["policies"])
async def get_policy(
    module_name: str,
    current_user = Depends(require_superuser),
    policy_service: PolicyService = Depends(get_policy_service)
):
    """Get a specific policy module"""
    rego_code = await policy_service.get_policy(module_name)
    
    if rego_code is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return PolicyResponse(module_name=module_name, rego_code=rego_code)

@router.delete("/policies/{module_name}", tags=["policies"])
async def delete_policy(
    module_name: str,
    current_user = Depends(require_superuser),
    policy_service: PolicyService = Depends(get_policy_service)
):
    """Delete a policy module"""
    success = await policy_service.delete_policy(module_name)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete policy")
    
    return {"message": f"Policy {module_name} deleted successfully"}
```

### Step 4: Register Router

```python
# python_apps/auth_api/app/main.py

from app.routers import policies

app.include_router(policies.router, prefix="/api", tags=["policies"])
```

---

## 🎨 Usage Examples

### Example 1: Generate Policy for Workflow Service

```bash
curl -X POST http://localhost:8004/auth-api/api/policies/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <superuser-token>" \
  -d '{
    "service_name": "workflow_engine",
    "resource_type": "workflow",
    "actions": {
      "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow"],
      "editor": ["create_workflow", "edit_workflow", "view_workflow"],
      "viewer": ["view_workflow"]
    }
  }'
```

### Example 2: Upload Custom Policy

```bash
curl -X POST http://localhost:8004/auth-api/api/policies/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <superuser-token>" \
  -d '{
    "module_name": "rbac/custom_rules",
    "rego_code": "package rbac\n\nimport rego.v1\n\nrole_check(assignment) if {\n  assignment.role == \"analyst\"\n  input.action == \"export_data\"\n}"
  }'
```

### Example 3: List All Policies

```bash
curl http://localhost:8004/auth-api/api/policies \
  -H "Authorization: Bearer <superuser-token>"

# Response:
{
  "policies": [
    "rbac/core",
    "rbac/workflow_engine",
    "rbac/agents",
    "rbac/custom_rules"
  ]
}
```

### Example 4: Get Specific Policy

```bash
curl http://localhost:8004/auth-api/api/policies/rbac/workflow_engine \
  -H "Authorization: Bearer <superuser-token>"
```

---

## 💾 Option 2: Database-Backed Policies

For even more flexibility, store policy rules in the database:

### Database Schema

```sql
CREATE TABLE policy_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(service_name, resource_type, role, action)
);

CREATE INDEX idx_policy_rules_service ON policy_rules(service_name);
CREATE INDEX idx_policy_rules_resource ON policy_rules(resource_type);
```

### Generate Rego from Database

```python
async def generate_rego_from_database():
    """Generate complete rego policy from database rules"""
    
    # Get all active rules
    rules = await db.execute(
        "SELECT * FROM policy_rules WHERE is_active = true ORDER BY service_name, role"
    )
    
    # Group by service and role
    services = {}
    for rule in rules:
        service = rule.service_name
        if service not in services:
            services[service] = {}
        
        role = rule.role
        if role not in services[service]:
            services[service][role] = []
        
        services[service][role].append(rule.action)
    
    # Generate rego for each service
    for service_name, roles in services.items():
        rego_code = await policy_service.generate_service_policy(
            service_name=service_name,
            resource_type=service_name,  # Or get from rules
            actions=roles
        )
        
        await policy_service.upload_policy(f"rbac/{service_name}", rego_code)
```

---

## 🎯 Recommended Approach

### Hybrid: Core + Dynamic

1. **Core policy** (static file): User status, basic role hierarchy
2. **Service policies** (dynamic): Generated from database or API

```
OPA Policies:
├── rbac/core.rego           (Static - user_is_active, base rules)
├── rbac/workflows.rego      (Dynamic - generated from DB/API)
├── rbac/agents.rego         (Dynamic - generated from DB/API)
└── rbac/custom.rego         (Dynamic - admin-defined rules)
```

### Core Policy (Always Loaded)

```rego
# rbac/core.rego - Never changes
package rbac

import rego.v1

default allow := false

allow if {
    user_is_active
    some assignment in input.user.assignments
    valid_resource_match(assignment)
    role_check(assignment)
}

user_is_active if {
    input.user.status == "active"
}

# Superadmin can do everything
role_check(assignment) if {
    assignment.role == "superadmin"
}

# Other role_check and valid_resource_match rules come from dynamic modules
```

---

## 🔒 Security Considerations

### 1. Restrict Policy Management

```python
@router.post("/policies/upload")
async def upload_policy(
    data: PolicyUpload,
    current_user = Depends(require_superuser)  # Only superusers!
):
    # Validate rego syntax before uploading
    if not validate_rego_syntax(data.rego_code):
        raise HTTPException(status_code=400, detail="Invalid rego syntax")
    
    # Audit log
    await log_policy_change(current_user.id, "upload", data.module_name)
    
    # Upload
    await policy_service.upload_policy(data.module_name, data.rego_code)
```

### 2. Validate Rego Syntax

```python
async def validate_rego_syntax(rego_code: str) -> bool:
    """Validate rego syntax using OPA"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{opa_url}/v1/compile",
            json={"query": "data.rbac.allow", "input": {}, "unknowns": ["input"]},
            headers={"Content-Type": "application/json"}
        )
        return response.status_code == 200
```

### 3. Audit Logging

```sql
CREATE TABLE policy_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50),  -- 'upload', 'delete', 'update'
    module_name VARCHAR(200),
    rego_code TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 🎊 Summary

**Yes, you can update rego via API!**

**Best approach for you:**
1. ✅ Use OPA Policy API for dynamic updates
2. ✅ Store policy rules in database for admin UI
3. ✅ Generate rego from database rules
4. ✅ Upload to OPA via API
5. ✅ No redeployment needed!

**Benefits:**
- Admins can add new services via UI
- No code deployment required
- Policies versioned in database
- Audit trail of all changes
- Can have per-service policy modules

**Next step:** Implement the policy management API and build an admin UI! 🚀

