# Auth API Testing Guide

This guide covers how to run integration tests for the Auth API with proper email testing.

## Quick Start

### 1. Start Test Environment

```bash
cd python_apps/auth_api
./scripts/start-test-env.sh
```

This will:
- Start PostgreSQL on port 5434
- Start MailHog SMTP server on port 1025 (Web UI on port 8025)
- Run database migrations
- Display connection info

### 2. Start Auth API with Test Configuration

```bash
cd python_apps/auth_api
export $(cat .env.test | grep -v '^#' | xargs)
python -m app.main
```

The Auth API will now:
- Connect to test PostgreSQL database
- Send all emails to MailHog (no real emails sent!)
- Use test API keys for integration tests

### 3. Run Integration Tests

```bash
cd python_packages/rbac-sdk
pytest tests/integration/ -v
```

### 4. View Captured Emails

Open http://localhost:8025 in your browser to see all emails sent during testing.

## Email Testing with MailHog

### What is MailHog?

MailHog is a lightweight SMTP server that:
- Catches ALL emails sent to it
- Provides a web UI to view emails
- Never sends emails to real recipients
- Perfect for testing without spamming

### Accessing MailHog

- **Web UI**: http://localhost:8025
- **SMTP Server**: localhost:1025

### Features

- View all captured emails in real-time
- Search emails by recipient, subject, etc.
- View HTML and plain text versions
- Download email content
- Delete emails
- API access for automated testing

### Testing Email Functionality

You can verify emails are being sent correctly:

1. **Register a new user** → Check MailHog for verification email
2. **Reset password** → Check MailHog for reset email
3. **MFA codes** → Check MailHog for MFA code email

Example test:
```python
import httpx

async def test_registration_sends_email():
    # Register user
    response = await client.post(
        "http://localhost:8004/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    
    # Check MailHog for email
    mailhog_response = await client.get("http://localhost:8025/api/v2/messages")
    messages = mailhog_response.json()
    
    # Verify email was sent
    assert len(messages["items"]) > 0
    latest_email = messages["items"][0]
    assert "test@example.com" in latest_email["To"]
    assert "verify" in latest_email["Subject"].lower()
```

## Environment Configuration

### Test Environment (.env.test)

The test environment uses:
- **PostgreSQL**: localhost:5433 (separate from dev database)
- **MailHog SMTP**: localhost:1025 (catches all emails)
- **API Key Secret**: `test-secret-key-for-integration-tests`
- **No TLS**: SMTP_TLS=false (MailHog doesn't require TLS)

### Production Environment

Production uses:
- Real SMTP server (Gmail, SendGrid, etc.)
- TLS/SSL encryption
- Real email addresses
- Secure API keys

## Stopping Test Environment

```bash
cd python_apps/auth_api
docker-compose -f docker-compose.test.yaml down
```

To also remove volumes (clean database):
```bash
docker-compose -f docker-compose.test.yaml down -v
```

## Troubleshooting

### MailHog not receiving emails

Check SMTP configuration:
```bash
echo $SMTP_HOST  # Should be: localhost
echo $SMTP_PORT  # Should be: 1025
echo $SMTP_TLS   # Should be: false
```

### PostgreSQL connection errors

Check if PostgreSQL is running:
```bash
docker ps | grep postgres-test
```

Check connection:
```bash
psql postgresql://auth_user:auth_password@localhost:5433/auth_db -c "SELECT 1"
```

### Integration tests failing

1. Ensure Auth API is running with test config
2. Check MailHog is running: http://localhost:8025
3. Check PostgreSQL is running: `docker ps`
4. Verify environment variables are set:
   ```bash
   echo $API_KEY_SECRET  # Should be: test-secret-key-for-integration-tests
   ```

## Advanced: Testing Email Content

### Using MailHog API

MailHog provides a REST API for automated testing:

```python
import httpx

async def get_latest_email():
    """Get the most recent email from MailHog."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8025/api/v2/messages")
        messages = response.json()
        if messages["items"]:
            return messages["items"][0]
    return None

async def search_emails(query: str):
    """Search emails in MailHog."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8025/api/v2/search?kind=containing&query={query}"
        )
        return response.json()

async def delete_all_emails():
    """Clear all emails from MailHog."""
    async with httpx.AsyncClient() as client:
        await client.delete("http://localhost:8025/api/v1/messages")
```

### Example Integration Test with Email Verification

```python
import pytest
import httpx
from datetime import datetime

@pytest.mark.asyncio
async def test_user_registration_with_email_verification():
    """Test that user registration sends verification email."""
    
    # Clear previous emails
    async with httpx.AsyncClient() as client:
        await client.delete("http://localhost:8025/api/v1/messages")
    
    # Register new user
    timestamp = datetime.now().timestamp()
    email = f"test-{timestamp}@example.com"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/api/auth/register",
            json={
                "email": email,
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
    
    # Wait a moment for email to be sent
    await asyncio.sleep(1)
    
    # Check MailHog for verification email
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8025/api/v2/messages")
        messages = response.json()
    
    # Verify email was sent
    assert len(messages["items"]) == 1
    email_data = messages["items"][0]
    
    # Verify email details
    assert email in str(email_data["To"])
    assert "verify" in email_data["Subject"].lower()
    
    # Verify email content contains verification link
    html_content = email_data["Content"]["Body"]
    assert "verify-email" in html_content
    assert "token=" in html_content
```

## CI/CD Integration

For CI/CD pipelines, you can use the same setup:

```yaml
# .github/workflows/test.yml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: auth_user
      POSTGRES_PASSWORD: auth_password
      POSTGRES_DB: auth_db
    ports:
      - 5433:5432
  
  mailhog:
    image: mailhog/mailhog
    ports:
      - 1025:1025
      - 8025:8025
```

## Summary

- ✅ **MailHog catches all emails** - No spam, no real emails sent
- ✅ **Web UI for inspection** - Easy to verify email content
- ✅ **API for automation** - Test email content programmatically
- ✅ **Isolated test environment** - Separate database and SMTP
- ✅ **Production-like testing** - Real SMTP protocol, just captured

