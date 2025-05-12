# Native Authentication API

A secure FastAPI-based authentication service with modern security features.

## Features

- User registration and management
- Secure password handling with Argon2id hashing
- JWT-based authentication with access and refresh tokens
- Email verification
- Password reset flow
- Multi-factor authentication (TOTP)
- Session management and device tracking
- Rate limiting to prevent brute force attacks
- Comprehensive audit logging

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

## Environment Variables

| Variable                    | Description                              | Default                                                    |
| --------------------------- | ---------------------------------------- | ---------------------------------------------------------- |
| SECRET_KEY                  | JWT signing key                          | Random value                                               |
| DATABASE_URI                | PostgreSQL connection URI                | postgresql+asyncpg://postgres:postgres@localhost:5433/auth |
| DEBUG                       | Debug mode                               | False                                                      |
| CORS_ORIGINS                | CORS allowed origins                     | []                                                         |
| ALLOWED_HOSTS               | Allowed hosts for TrustedHost middleware | ["localhost", "127.0.0.1"]                                 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token expiration time             | 30                                                         |
| REFRESH_TOKEN_EXPIRE_DAYS   | Refresh token expiration time            | 7                                                          |
| FRONTEND_URL                | Frontend URL for links in emails         | None                                                       |
| SMTP_TLS                    | Whether to use TLS for SMTP              | True                                                       |
| SMTP_PORT                   | SMTP port                                | 587                                                        |
| SMTP_HOST                   | SMTP server hostname                     | "outbound.mailhop.org"                                     |
| SMTP_USER                   | SMTP username                            | "elevaite"                                                 |
| SMTP_PASSWORD               | SMTP password                            | ""                                                         |
| EMAILS_FROM_EMAIL           | Sender email address                     | "noreply@iopex.com"                                        |
| EMAILS_FROM_NAME            | Sender name                              | "ElevAIte"                                                 |

## Docker

Build and run with Docker:

```bash
docker build -t auth-api .
docker run -p 8000:8000 --env-file .env auth-api
```
