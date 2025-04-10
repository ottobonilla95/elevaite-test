"""Application configuration."""

import secrets
from typing import List, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

    # API Settings
    PROJECT_NAME: str = "Auth API"
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # 32-bytes key for HMAC operations (e.g., CSRF token)
    SECURITY_KEY: str = secrets.token_urlsafe(32)

    # Password security
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # 2FA
    MFA_ISSUER: str = "AuthAPI"
    MFA_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Trusted hosts
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # Database
    DATABASE_URI: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/auth"

    # Email settings for password resets, etc.
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@example.com"
    EMAILS_FROM_NAME: str = "Auth API"

    @validator("CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, list):
            return v
        raise ValueError("CORS_ORIGINS should be a comma-separated string or a list")


settings = Settings()
