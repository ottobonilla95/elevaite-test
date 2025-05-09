import os
import secrets
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings."""

    load_dotenv()
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # API Settings
    PROJECT_NAME: str = "Auth API"
    API_PREFIX: str = "/api"
    _debug_env = os.environ.get("DEBUG")
    DEBUG: bool = _debug_env is not None

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
    CORS_ORIGINS: List[str] = []

    # Trusted hosts
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # Database
    @property
    def DATABASE_URI(self) -> str:
        _database_env = os.environ.get("SQLALCHEMY_DATABASE_URL")
        if not _database_env:
            raise ValueError("SQLALCHEMY_DATABASE_URL environment variable is not set")
        return _database_env

    # Frontend URL for links in emails
    @property
    def FRONTEND_URI(self) -> str:
        _frontend_env = os.environ.get("FRONTEND_URL")
        if not _frontend_env:
            raise ValueError("FRONTEND_URL environment variable is not set")
        return _frontend_env

    # Email settings for SendGrid API
    SMTP_USER: str = "apikey"
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: str = os.environ.get("EMAILS_FROM_EMAIL", "noreply@iopex.com")
    EMAILS_FROM_NAME: str = os.environ.get("EMAILS_FROM_NAME", "ElevAIte")

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, list):
            return v
        raise ValueError("CORS_ORIGINS should be a comma-separated string or a list")


settings = Settings()
