# Auth API with Authorization - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will get you up and running with the unified Auth API that now includes authorization (RBAC + OPA).

---

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL client (optional, for manual DB access)

---

## Step 1: Start the Services

```bash
cd python_apps/auth_api

# Start Auth API, OPA, and PostgreSQL
docker-compose -f docker-compose.dev.yaml up -d

# Check logs
docker-compose -f docker-compose.dev.yaml logs -f
```

**Services:**
- Auth API: http://localhost:8004
- OPA: http://localhost:8181
- PostgreSQL: localhost:5433

---

## Step 2: Run Database Migrations

```bash
# Run migrations to create RBAC tables
docker-compose -f docker-compose.dev.yaml exec auth_api alembic upgrade head
```

This creates:
- `organizations`
- `accounts`
- `projects`
- `user_role_assignments`

---

## Step 3: Create Test Data

### Create a User (via Auth API)

```bash
curl -X POST http://localhost:8004/auth-api/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "status": "active",
  "is_verified": false
}
```

### Create an Organization

```bash
# First, login as superuser to get token
# (You'll need to create a superuser first or use existing admin)

curl -X POST http://localhost:8004/auth-api/api/rbac/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Acme Corp",
    "description": "Test organization"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corp",
  "description": "Test organization",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### Create an Account

```bash
curl -X POST http://localhost:8004/auth-api/api/rbac/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Engineering",
    "description": "Engineering team"
  }'
```

### Create a Project

```bash
curl -X POST http://localhost:8004/auth-api/api/rbac/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "account_id": "ACCOUNT_ID_FROM_PREVIOUS_STEP",
    "name": "Project Alpha",
    "description": "Our first project"
  }'
```

### Assign a Role to User

```bash
curl -X POST http://localhost:8004/auth-api/api/rbac/user_role_assignments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_id": 1,
    "role": "viewer",
    "resource_type": "project",
    "resource_id": "PROJECT_ID_FROM_PREVIOUS_STEP"
  }'
```

---

## Step 4: Test Authorization

### Check Access (User is Active)

```bash
curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "view_project",
    "resource": {
      "type": "project",
      "id": "PROJECT_ID",
      "organization_id": "ORG_ID",
      "account_id": "ACCOUNT_ID"
    }
  }'
```

**Response (Allowed):**
```json
{
  "allowed": true,
  "deny_reason": null,
  "user_status": "active"
}
```

### Test Security Fix: Deactivate User

```bash
# Update user status to inactive (requires DB access or admin endpoint)
# For testing, you can do this directly in the database:

docker-compose -f docker-compose.dev.yaml exec db psql -U auth_user -d auth_db -c \
  "UPDATE users SET status = 'inactive' WHERE id = 1;"
```

### Check Access Again (User is Inactive)

```bash
curl -X POST http://localhost:8004/auth-api/api/authz/check_access \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "action": "view_project",
    "resource": {
      "type": "project",
      "id": "PROJECT_ID",
      "organization_id": "ORG_ID",
      "account_id": "ACCOUNT_ID"
    }
  }'
```

**Response (Denied - Security Fix Working!):**
```json
{
  "allowed": false,
  "deny_reason": "user_not_active",
  "user_status": "inactive"
}
```

🎉 **The security hole is fixed!** Inactive users are immediately denied access.

---

## Step 5: Use the rbac-sdk

### Install the SDK

```bash
# In your service that needs to check authorization
pip install -e /path/to/python_packages/rbac-sdk
```

### Use in Your Code

```python
from rbac_sdk import check_access
import os

# Set the Auth API URL
os.environ["AUTHZ_SERVICE_URL"] = "http://localhost:8004/auth-api"

# Check if user can view a project
allowed = check_access(
    user_id=1,
    action="view_project",
    resource={
        "type": "project",
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "organization_id": "550e8400-e29b-41d4-a716-446655440001",
        "account_id": "550e8400-e29b-41d4-a716-446655440002"
    }
)

if allowed:
    print("✅ Access granted!")
else:
    print("❌ Access denied!")
```

### Async Version

```python
from rbac_sdk import check_access_async

allowed = await check_access_async(
    user_id=1,
    action="edit_project",
    resource={
        "type": "project",
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "organization_id": "550e8400-e29b-41d4-a716-446655440001",
        "account_id": "550e8400-e29b-41d4-a716-446655440002"
    }
)
```

---

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8004/auth-api/docs
- **ReDoc:** http://localhost:8004/auth-api/redoc

---

## Troubleshooting

### OPA Not Starting

```bash
# Check OPA logs
docker-compose -f docker-compose.dev.yaml logs opa

# Test OPA directly
curl http://localhost:8181/health
```

### Database Connection Issues

```bash
# Check database logs
docker-compose -f docker-compose.dev.yaml logs db

# Connect to database manually
docker-compose -f docker-compose.dev.yaml exec db psql -U auth_user -d auth_db
```

### Auth API Not Starting

```bash
# Check Auth API logs
docker-compose -f docker-compose.dev.yaml logs auth_api

# Restart services
docker-compose -f docker-compose.dev.yaml restart
```

---

## Environment Variables

Key environment variables (set in `docker-compose.dev.yaml`):

```bash
# Database
SQLALCHEMY_DATABASE_URL=postgresql://auth_user:auth_pass@db:5432/auth_db

# OPA
OPA_URL=http://opa:8181/v1/data/rbac/allow
OPA_ENABLED=true
OPA_TIMEOUT=5.0

# Auth
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=90
REFRESH_TOKEN_EXPIRE_MINUTES=10080

# Frontend
FRONTEND_URL=http://localhost:3000
```

---

## Next Steps

1. **Write Tests** - Add unit and integration tests
2. **Add More Roles** - Extend OPA policy for custom roles
3. **Integrate with Your Services** - Use rbac-sdk in your applications
4. **Monitor** - Set up logging and monitoring for authorization decisions
5. **Production** - Deploy with proper secrets and scaling

---

## 🎊 You're All Set!

The unified Auth API with authorization is now running. You have:
- ✅ Authentication (login, MFA, sessions)
- ✅ Authorization (RBAC with OPA)
- ✅ User status validation (security fix!)
- ✅ Complete API for managing organizations, accounts, projects, and roles

Happy coding! 🚀

