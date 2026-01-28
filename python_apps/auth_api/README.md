# Authentication API

A secure FastAPI-based authentication service with dual authentication providers and modern security features.

## Features

### Core Authentication

- **Dual Authentication Providers**: Native JWT and AWS Cognito
- User registration and management
- Secure password handling with Argon2id hashing
- JWT-based authentication with access and refresh tokens
- Email verification and password reset flows
- Multi-factor authentication (TOTP)
- Session management and device tracking
- Rate limiting to prevent brute force attacks
- Comprehensive audit logging

### SMS MFA Integration

- SMS-based Multi-Factor Authentication using AWS SNS
- Works with existing user system (no external user pools needed)
- Simple setup, verification, and disable endpoints
- Phone number validation and formatting
- Redis-based temporary code storage

## Security Features

- Argon2id password hashing (more secure than bcrypt)
- JWT with proper signing and expiration
- TOTP-based 2FA
- Strong password policies
- Account locking after failed login attempts
- Session tracking and revocation
- CSRF protection
- Comprehensive security headers
- Rate limiting
- Audit logging

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

1. Clone the repository
2. Install dependencies:

   ```
   uv venv
   uv pip install -e .
   ```

3. Set up environment variables (create a `.env` file or set them directly)
4. Run database migrations:

   ```
   alembic upgrade head
   ```

5. Start the server:
   ```
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Native Authentication (`/api/auth/`)

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout
- `POST /api/auth/verify-email` - Verify email
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token
- `POST /api/auth/mfa/setup` - Set up MFA
- `POST /api/auth/mfa/activate` - Activate MFA
- `GET /api/auth/sessions` - List active sessions
- `DELETE /api/auth/sessions/{id}` - Revoke a session

### SMS MFA (`/api/sms-mfa/`)

- `POST /api/sms-mfa/setup` - Setup SMS MFA with phone number
- `POST /api/sms-mfa/send-code` - Send MFA code to user's phone
- `POST /api/sms-mfa/verify` - Verify MFA code
- `POST /api/sms-mfa/disable` - Disable SMS MFA for user

## Configuration

### Environment Files

The Auth API uses different environment files for different purposes:

- **`.env.local.example`** - Template for local development with MailHog email testing
  - Copy to `.env` for local development
  - Uses MailHog (localhost:1025) for email testing
  - Uses test JWT keys (DO NOT use in production!)
  - Safe for integration testing

- **`.env.test`** - Configuration for automated integration tests
  - Used by pytest integration tests
  - Uses MailHog for email testing
  - Uses test database and test JWT keys

- **`.env.production.template`** - Template for production deployment
  - Copy to `.env.production` and fill in real values
  - **IMPORTANT:** Uses real SMTP server (NOT MailHog!)
  - Requires strong, randomly generated SECRET_KEY
  - Never commit `.env.production` to git!

### Setting Up for Local Development

1. Copy the local development template:
   ```bash
   cp .env.local.example .env
   ```

2. Start MailHog for email testing:
   ```bash
   docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
   ```

3. Access MailHog web UI at http://localhost:8025 to view test emails

### Setting Up for Production

1. Copy the production template:
   ```bash
   cp .env.production.template .env.production
   ```

2. Generate secure keys:
   ```bash
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
   python -c "import secrets; print('API_KEY_SECRET=' + secrets.token_urlsafe(32))"
   ```

3. Configure real SMTP server (Gmail, SendGrid, AWS SES, etc.)
   - **DO NOT use MailHog in production!**
   - Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_TLS=True`
   - Set `SMTP_USER` and `SMTP_PASSWORD` with real credentials

4. Update database URL, CORS origins, and other production settings

### Environment Variables

#### Core Settings

```bash
# Database
SQLALCHEMY_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5433/auth"

# JWT Settings (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY="your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
REFRESH_TOKEN_EXPIRE_DAYS="7"

# Email Settings (DO NOT use MailHog in production!)
SMTP_HOST="smtp.gmail.com"  # Use real SMTP server
SMTP_PORT="587"
SMTP_TLS="True"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-specific-password"
EMAILS_FROM_EMAIL="noreply@yourdomain.com"

# Frontend URL
FRONTEND_URL="http://localhost:3002"
```

## SMS MFA with AWS SNS

SMS MFA uses AWS SNS to send verification codes. See [AWS SMS Setup Guide](docs/AWS_SMS_SETUP.md) for configuration details.

### Quick Setup

1. Set up AWS Cognito User Pool with email verification
2. Create User Pool Client with client secret
3. Configure environment variables in `.env.local`
4. Set `AUTH_PROVIDER="both"` to enable dual authentication

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run Cognito-specific tests
python tests/test_cognito_runner.py

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v
```
# Force rebuild
# Force rebuild Tue 27 Jan 2026 23:45:45 -05
