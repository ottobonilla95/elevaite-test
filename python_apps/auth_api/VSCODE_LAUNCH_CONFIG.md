# VSCode Launch Configuration for Auth API

## 🚀 Quick Setup

Add this configuration to your `.vscode/launch.json` to debug the Auth API in VSCode:

```json
{
    "name": "Elevaite | Auth API",
    "type": "debugpy",
    "request": "launch",
    "module": "uvicorn",
    "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8004"
    ],
    "jinja": true,
    "justMyCode": true,
    "cwd": "${workspaceFolder}/python_apps/auth_api",
    "env": {
        "SQLALCHEMY_DATABASE_URL": "postgresql+asyncpg://elevaite:elevaite@localhost:5433/auth",
        "FRONTEND_URL": "http://localhost:3002",
        "SECRET_KEY": "SECRET_KEY",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "90",
        "REFRESH_TOKEN_EXPIRE_MINUTES": "90",
        "SMTP_TLS": "True",
        "SMTP_PORT": "587",
        "SMTP_HOST": "outbound.mailhop.org",
        "SMTP_USER": "elevaite",
        "SMTP_PASSWORD": "SMTP_PASSWORD",
        "EMAILS_FROM_EMAIL": "noreply@iopex.ai",
        "EMAILS_FROM_NAME": "iOPEX AI",
        "RATE_LIMIT_PER_MINUTE": "60",
        "MFA_DEVICE_BYPASS_HOURS": "24",
        "CORS_ORIGINS": "[\"http://localhost:3002\", \"http://localhost:8004\"]",
        "ALLOWED_HOSTS": "[\"localhost\", \"127.0.0.1\"]",
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "your-aws-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "your-aws-secret-access-key",
        "SMS_SENDER_ID": "",
        "EMAIL_MFA_GRACE_PERIOD_DAYS": "30",
        "MFA_AUTO_ENABLE_METHOD": "email",
        "MFA_EMAIL_PRIMARY_COLOR": "e75f33",
        "BRANDING_NAME": "ElevAIte",
        "BRANDING_ORG": "iOPEX",
        "BRANDING_SUPPORT_EMAIL": "support@iopex.ai",
        "OPA_URL": "http://localhost:8181/v1/data/rbac/allow",
        "OPA_ENABLED": "true",
        "OPA_TIMEOUT": "5.0"
    }
}
```

---

## 📋 Environment Variables Explained

### Database
- **`SQLALCHEMY_DATABASE_URL`**: PostgreSQL connection string (async driver)
  - Default: `postgresql+asyncpg://elevaite:elevaite@localhost:5433/auth`

### Frontend Integration
- **`FRONTEND_URL`**: URL for email links and redirects
  - Default: `http://localhost:3002`

### JWT Authentication
- **`SECRET_KEY`**: Secret key for JWT token signing
- **`ACCESS_TOKEN_EXPIRE_MINUTES`**: Access token expiration (default: 90)
- **`REFRESH_TOKEN_EXPIRE_MINUTES`**: Refresh token expiration (default: 90)

### Email Configuration
- **`SMTP_TLS`**: Enable TLS for SMTP (default: True)
- **`SMTP_PORT`**: SMTP server port (default: 587)
- **`SMTP_HOST`**: SMTP server hostname
- **`SMTP_USER`**: SMTP username
- **`SMTP_PASSWORD`**: SMTP password
- **`EMAILS_FROM_EMAIL`**: Sender email address
- **`EMAILS_FROM_NAME`**: Sender display name

### Rate Limiting
- **`RATE_LIMIT_PER_MINUTE`**: General rate limit (default: 60)

### MFA Configuration
- **`MFA_DEVICE_BYPASS_HOURS`**: Hours to remember trusted devices (default: 24)
- **`EMAIL_MFA_GRACE_PERIOD_DAYS`**: Grace period for email MFA (default: 30)
- **`MFA_AUTO_ENABLE_METHOD`**: Auto-enable MFA method (email/sms/totp/none)
- **`MFA_EMAIL_PRIMARY_COLOR`**: Primary color for MFA emails (hex without #)

### AWS (for SMS MFA)
- **`AWS_REGION`**: AWS region for SNS (default: us-east-1)
- **`AWS_ACCESS_KEY_ID`**: AWS access key
- **`AWS_SECRET_ACCESS_KEY`**: AWS secret key
- **`SMS_SENDER_ID`**: Custom sender ID for SMS (optional)

### Security
- **`CORS_ORIGINS`**: Allowed CORS origins (JSON array string)
- **`ALLOWED_HOSTS`**: Allowed host headers (JSON array string)

### Branding
- **`BRANDING_NAME`**: Application name (default: ElevAIte)
- **`BRANDING_ORG`**: Organization name (default: iOPEX)
- **`BRANDING_SUPPORT_EMAIL`**: Support email address

### OPA (Open Policy Agent) - NEW! 🆕
- **`OPA_URL`**: OPA endpoint for authorization checks
  - Default: `http://localhost:8181/v1/data/rbac/allow`
- **`OPA_ENABLED`**: Enable/disable OPA integration (default: true)
- **`OPA_TIMEOUT`**: Timeout for OPA requests in seconds (default: 5.0)

---

## 🔧 Prerequisites

Before running the Auth API in VSCode:

1. **Database Running**
   ```bash
   # Make sure PostgreSQL is running on port 5433
   # Database "auth" should exist
   ```

2. **OPA Running** (if `OPA_ENABLED=true`)
   ```bash
   # Start OPA with the RBAC policy
   docker run -d -p 8181:8181 openpolicyagent/opa:latest \
     run --server --addr :8181
   
   # Or use docker-compose.dev.yaml
   cd python_apps/auth_api
   docker compose -f docker-compose.dev.yaml up -d opa
   ```

3. **Python Environment**
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Install dependencies
   cd python_apps/auth_api
   pip install -r requirements.txt
   ```

---

## 🎯 Usage

1. Open VSCode
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select "Elevaite | Auth API" from the dropdown
4. Press F5 or click the green play button
5. API will start on http://localhost:8004
6. Swagger docs available at http://localhost:8004/docs

---

## 🐛 Debugging

- Set breakpoints in your code
- Use the Debug Console to inspect variables
- Step through code with F10 (step over) and F11 (step into)
- View call stack and variables in the Debug sidebar

---

## 📝 Notes

- The `.vscode` directory is gitignored, so this config is local to your machine
- Update environment variables as needed for your local setup
- For production, use proper secrets management (not hardcoded values)
- OPA can be disabled by setting `OPA_ENABLED=false` if not needed for local dev

