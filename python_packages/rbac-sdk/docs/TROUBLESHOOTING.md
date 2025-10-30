# RBAC SDK Troubleshooting Guide

Common issues and solutions when using the RBAC SDK.

## Table of Contents

- [Configuration Issues](#configuration-issues)
- [Authentication Issues](#authentication-issues)
- [Authorization Issues](#authorization-issues)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)

## Configuration Issues

### Error: "AUTH_API_BASE must be set or base_url provided"

**Problem:** The SDK cannot find the Auth API base URL.

**Solution:**
```bash
# Set environment variable
export AUTH_API_BASE="http://localhost:8004"

# Or provide base_url in code
validator = api_key_http_validator(base_url="http://localhost:8004")
```

### Error: "AUTHZ_SERVICE_URL must be set or base_url provided"

**Problem:** The SDK cannot find the OPA service URL.

**Solution:**
```bash
# Set environment variable
export AUTHZ_SERVICE_URL="http://localhost:8181"

# Or provide base_url in code
guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
    base_url="http://localhost:8181",
)
```

### Error: "API_KEY_SECRET must be set"

**Problem:** JWT API key validation requires a secret key.

**Solution:**
```bash
# Set environment variable
export API_KEY_SECRET="your-secret-key-here"
export API_KEY_ALGORITHM="HS256"

# Or provide in code
validator = api_key_jwt_validator(
    algorithm="HS256",
    secret="your-secret-key-here",
)
```

## Authentication Issues

### Error: "Missing X-elevAIte-UserId header" (401)

**Problem:** The request doesn't include a user ID header.

**Solution:**
```python
# Include user ID header in requests
headers = {
    "X-elevAIte-UserId": "user-123",
    "X-elevAIte-ProjectId": "proj-uuid",
    "X-elevAIte-OrganizationId": "org-uuid",
}
```

### Error: "Missing X-elevAIte-apikey header" (401)

**Problem:** Using `api_key_or_user()` resolver but neither API key nor user ID is provided.

**Solution:**
```python
# Provide either API key OR user ID
headers = {
    "X-elevAIte-apikey": "your-api-key",
    # OR
    "X-elevAIte-UserId": "user-123",
    # Plus resource headers
    "X-elevAIte-ProjectId": "proj-uuid",
    "X-elevAIte-OrganizationId": "org-uuid",
}
```

### API Key Validation Returns None

**Problem:** API key validation fails silently.

**Possible Causes:**
1. API key is invalid or expired
2. Auth API is down or unreachable
3. Wrong base URL configured

**Solution:**
```python
# Check Auth API is running
curl http://localhost:8004/api/health

# Test API key validation directly
curl -X POST http://localhost:8004/api/auth/validate-apikey \
  -H "X-elevAIte-apikey: your-api-key"

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### JWT Validation Fails

**Problem:** JWT API keys are rejected.

**Possible Causes:**
1. Wrong algorithm (HS256 vs RS256)
2. Wrong secret key
3. Token expired
4. Missing or wrong "type" claim

**Solution:**
```python
# Verify JWT structure
import jwt
token = "your-jwt-token"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)  # Check "sub", "type", "exp" claims

# Verify with correct secret
decoded = jwt.decode(token, "your-secret", algorithms=["HS256"])
```

## Authorization Issues

### Error: "Access denied" (403)

**Problem:** User doesn't have permission for the action.

**Debugging Steps:**

1. **Check user status:**
```python
# User must be "active"
# Check in Auth API database
SELECT id, email, status FROM users WHERE id = 'user-123';
```

2. **Check role assignments:**
```python
# User must have a role assignment
SELECT * FROM user_role_assignments WHERE user_id = 'user-123';
```

3. **Check OPA policy:**
```bash
# Test OPA directly
curl -X POST http://localhost:8181/v1/data/rbac/allow \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "user": {
        "id": "user-123",
        "status": "active",
        "assignments": [
          {"role": "viewer", "scope": "project", "resource_id": "proj-uuid"}
        ]
      },
      "action": "view_project",
      "resource": {
        "type": "project",
        "id": "proj-uuid",
        "organization_id": "org-uuid"
      }
    }
  }'
```

4. **Check action name:**
```python
# Make sure action matches OPA policy
# Common actions: view_project, edit_project, manage_account
guard = require_permission_async(
    action="view_project",  # Must match OPA policy
    ...
)
```

### Error: "Missing X-elevAIte-ProjectId header" (400)

**Problem:** Resource builder requires headers that aren't provided.

**Solution:**
```python
# Include all required headers
headers = {
    "X-elevAIte-ProjectId": "proj-uuid",      # Required
    "X-elevAIte-OrganizationId": "org-uuid",  # Required
    "X-elevAIte-AccountId": "acc-uuid",       # Optional
}
```

### Permissions Work in One Service But Not Another

**Problem:** Inconsistent behavior across services.

**Possible Causes:**
1. Different OPA URLs
2. Different role assignments in different databases
3. Different resource IDs

**Solution:**
```bash
# Verify all services use same OPA
echo $AUTHZ_SERVICE_URL  # Should be same everywhere

# Verify all services use same Auth API
echo $AUTH_API_BASE  # Should be same everywhere

# Check role assignments in correct database
# Make sure you're checking the right tenant/organization
```

## Performance Issues

### Slow API Key Validation

**Problem:** Every request is slow due to API key validation.

**Solution:**
```python
# Enable caching (default is 60 seconds)
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,  # Cache for 60 seconds
)

# Or use JWT validation (no HTTP call)
validator = api_key_jwt_validator(
    algorithm="HS256",
    secret="your-secret",
)
```

### High Memory Usage

**Problem:** Cache grows unbounded.

**Solution:**
```python
# Reduce cache TTL
validator = api_key_http_validator(
    cache_ttl=30.0,  # Shorter TTL = less memory
)

# Or disable caching
validator = api_key_http_validator(
    cache_ttl=0.0,  # No caching
)
```

### OPA Service Timeouts

**Problem:** Requests timeout waiting for OPA.

**Solution:**
```bash
# Check OPA is running
curl http://localhost:8181/health

# Check OPA performance
time curl -X POST http://localhost:8181/v1/data/rbac/allow -d '{"input": {...}}'

# Increase timeout if needed (not recommended)
# Better to fix OPA performance
```

## Integration Issues

### FastAPI Dependency Injection Not Working

**Problem:** Guard doesn't run or runs multiple times.

**Solution:**
```python
# Correct: Use dependencies parameter
@router.get("/projects", dependencies=[Depends(guard)])
async def list_projects():
    ...

# Incorrect: Don't call guard directly
@router.get("/projects")
async def list_projects(result=Depends(guard)):  # Wrong!
    ...
```

### Guard Runs But Doesn't Deny Access

**Problem:** Guard returns without raising exception.

**Possible Causes:**
1. OPA service is down (SDK fails open in some error cases)
2. Wrong base URL
3. Network issues

**Solution:**
```python
# Check OPA is reachable
import requests
response = requests.post(
    "http://localhost:8181/v1/data/rbac/allow",
    json={"input": {...}}
)
print(response.status_code, response.json())

# Enable fail-closed mode (recommended)
# SDK should fail closed by default, but verify OPA is running
```

### Multiple Guards on Same Endpoint

**Problem:** Need to check multiple permissions.

**Solution:**
```python
# Use multiple guards
@router.post(
    "/workflows/{id}/execute",
    dependencies=[
        Depends(guard_view_workflow),  # Must be able to view
        Depends(guard_execute_workflow),  # Must be able to execute
    ]
)
async def execute_workflow(id: str):
    ...
```

### Custom Resource Builder Not Working

**Problem:** Custom resource builder raises errors.

**Solution:**
```python
# Make sure it returns correct structure
def custom_builder(request: Request) -> Dict[str, Any]:
    return {
        "type": "project",  # Required
        "id": "...",  # Required
        "organization_id": "...",  # Required
        "account_id": "...",  # Optional
    }

# Make sure it raises HTTPException for errors
from fastapi import HTTPException

def custom_builder(request: Request) -> Dict[str, Any]:
    project_id = request.headers.get("X-Project-ID")
    if not project_id:
        raise HTTPException(status_code=400, detail="Missing X-Project-ID")
    return {"type": "project", "id": project_id, ...}
```

## Getting Help

If you're still stuck:

1. **Check logs:** Enable DEBUG logging to see what's happening
2. **Test components individually:** Test Auth API, OPA, and SDK separately
3. **Check examples:** See `python_apps/workflow-engine-poc` for working examples
4. **Review tests:** See `python_packages/rbac-sdk/tests/` for usage patterns

## Common Patterns

### Testing Without Auth

For local development/testing:

```python
# Option 1: Use insecure mode (NOT for production)
os.environ["RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL"] = "true"

# Option 2: Mock the guard
from unittest.mock import Mock

async def mock_guard(request: Request):
    pass  # Always allow

@router.get("/projects", dependencies=[Depends(mock_guard)])
async def list_projects():
    ...
```

### Debugging Access Denials

```python
# Add logging to see why access was denied
import logging
logging.basicConfig(level=logging.DEBUG)

# Check OPA response directly
from rbac_sdk import check_access_async

allowed = await check_access_async(
    user_id="user-123",
    action="view_project",
    resource={"type": "project", "id": "proj-uuid", "organization_id": "org-uuid"}
)
print(f"Access allowed: {allowed}")
```

