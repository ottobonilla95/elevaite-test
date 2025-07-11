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

### Environment Variables

#### Core Settings

```bash
# Database
SQLALCHEMY_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5433/auth"

# JWT Settings
SECRET_KEY="your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
REFRESH_TOKEN_EXPIRE_DAYS="7"

# Email Settings
SMTP_HOST="your-smtp-host"
SMTP_USER="your-smtp-user"
SMTP_PASSWORD="your-smtp-password"
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
