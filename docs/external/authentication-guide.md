# Authentication Guide

Authentication, authorization, MFA, and RBAC for the elevAIte platform.

## Overview

The Auth API provides:
- JWT-based authentication
- Multi-factor authentication (TOTP, SMS, Email)
- Role-based access control (RBAC)
- API key authentication for services

---

## Login Flow

### Basic Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Token Usage

Include the access token in all API requests:

```http
GET /api/workflows
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Token Refresh

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Logout

```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

---

## Multi-Factor Authentication (MFA)

### MFA Required Response

When MFA is enabled, login returns `400` with MFA headers:

```http
HTTP/1.1 400 Bad Request
X-MFA-Type: TOTP
X-MFA-Methods: TOTP,SMS,EMAIL
```

**Response body:**
```json
{
  "detail": "MFA verification required",
  "mfa_required": true,
  "mfa_type": "TOTP"
}
```

### Complete MFA Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "mfa_code": "123456",
  "mfa_type": "TOTP"
}
```

### MFA Methods

| Method | Description |
|--------|-------------|
| `TOTP` | Time-based OTP via authenticator app |
| `SMS` | Code sent via SMS |
| `EMAIL` | Code sent via email |

### Setup TOTP

```http
POST /api/auth/mfa/totp/setup
Authorization: Bearer <token>
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/elevAIte:user@example.com?secret=..."
}
```

### Verify TOTP Setup

```http
POST /api/auth/mfa/totp/verify
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "123456"
}
```

### Request SMS/Email Code

```http
POST /api/sms-mfa/send
Content-Type: application/json

{
  "email": "user@example.com"
}
```

```http
POST /api/email-mfa/send
Content-Type: application/json

{
  "email": "user@example.com"
}
```

---

## User Registration

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
```json
{
  "id": "user-uuid",
  "email": "newuser@example.com",
  "is_active": true,
  "is_verified": false
}
```

### Email Verification

```http
POST /api/auth/verify-email
Content-Type: application/json

{
  "token": "verification-token-from-email"
}
```

---

## Password Management

### Forgot Password

```http
POST /api/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Reset Password

```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123!"
}
```

---

## Role-Based Access Control (RBAC)

### Required Headers

RBAC-protected endpoints require context headers:

| Header | Description |
|--------|-------------|
| `X-elevAIte-UserId` | Current user ID |
| `X-elevAIte-OrganizationId` | Organization context |
| `X-elevAIte-AccountId` | Account context (optional) |
| `X-elevAIte-ProjectId` | Project context (optional) |

### Check Access

```http
POST /api/authz/check-access
Content-Type: application/json
X-elevAIte-UserId: user-123
X-elevAIte-OrganizationId: org-xyz

{
  "resource_type": "workflow",
  "resource_id": "workflow-uuid",
  "action": "execute"
}
```

**Response:**
```json
{
  "allowed": true,
  "reason": "User has execute permission on workflow"
}
```

### Resource Types

| Resource | Actions |
|----------|---------|
| `workflow` | `create`, `read`, `update`, `delete`, `execute` |
| `agent` | `create`, `read`, `update`, `delete`, `execute` |
| `tool` | `create`, `read`, `update`, `delete`, `execute` |
| `prompt` | `create`, `read`, `update`, `delete` |
| `execution` | `read`, `cancel` |
| `user` | `create`, `read`, `update`, `delete` |
| `role` | `create`, `read`, `update`, `delete`, `assign` |

### Role Management

**List Roles:**
```http
GET /api/rbac/roles
X-elevAIte-OrganizationId: org-xyz
```

**Create Role:**
```http
POST /api/rbac/roles
Content-Type: application/json

{
  "name": "workflow_admin",
  "description": "Can manage workflows",
  "permissions": [
    {"resource_type": "workflow", "actions": ["create", "read", "update", "delete", "execute"]}
  ]
}
```

**Assign Role to User:**
```http
POST /api/rbac/users/{user_id}/roles
Content-Type: application/json

{
  "role_id": "role-uuid",
  "scope": {
    "organization_id": "org-xyz",
    "project_id": "proj-abc"
  }
}
```

---

## API Key Authentication

For service-to-service communication without user context.

### Create API Key

```http
POST /api/auth/api-keys
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Integration Service",
  "expires_in_days": 365,
  "scopes": ["workflows:execute", "agents:read"]
}
```

**Response:**
```json
{
  "id": "key-uuid",
  "api_key": "eyJhbGciOiJIUzI1NiIs...",
  "name": "Integration Service",
  "expires_at": "2025-01-15T00:00:00Z"
}
```

### Using API Keys

```http
POST /api/workflows/{id}/execute
X-elevAIte-apikey: eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{...}
```

### Validate API Key

```http
POST /api/auth/validate-apikey
X-elevAIte-apikey: eyJhbGciOiJIUzI1NiIs...
```

**Response:**
```json
{
  "valid": true,
  "user_id": "service-account-uuid",
  "scopes": ["workflows:execute", "agents:read"],
  "expires_at": "2025-01-15T00:00:00Z"
}
```

---

## JWT Token Structure

### Access Token Claims

| Claim | Description |
|-------|-------------|
| `sub` | User ID |
| `email` | User email |
| `type` | `access` or `refresh` |
| `exp` | Expiration timestamp |
| `iat` | Issued at timestamp |
| `tenant_id` | Tenant ID (if multi-tenant) |
| `roles` | Array of role IDs |

### Token Expiration

| Token Type | Default Expiration |
|------------|-------------------|
| Access Token | 1 hour |
| Refresh Token | 7 days |
| API Key | Configurable (up to 1 year) |

---

## Security Best Practices

1. **Store tokens securely** - Use httpOnly cookies or secure storage
2. **Refresh tokens proactively** - Before expiration
3. **Enable MFA** - For all production accounts
4. **Use API keys** - For service-to-service, not user auth
5. **Rotate API keys** - Regularly and on suspected compromise
6. **Scope API keys** - Minimum required permissions
7. **Monitor auth events** - Log and alert on suspicious activity

