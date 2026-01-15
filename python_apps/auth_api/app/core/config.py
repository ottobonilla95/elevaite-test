import os
import secrets
from typing import List, Union, Optional

from pydantic import field_validator, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    # Load environment files in order: .env first, then .env.local (which overrides .env)
    load_dotenv(".env")
    load_dotenv(".env.local", override=True)

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.local"],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # API Settings
    PROJECT_NAME: str = "Auth API"
    API_PREFIX: str = "/api"
    _debug_env = os.environ.get("DEBUG")
    DEBUG: bool = _debug_env is not None

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "180"))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", "43200"))
    ALGORITHM: str = "HS256"

    # API Key configuration
    API_KEY_ALGORITHM: str = os.environ.get("API_KEY_ALGORITHM", "HS256")  # e.g., HS256 or RS256
    API_KEY_SECRET: str | None = os.environ.get("API_KEY_SECRET")  # for HS*
    API_KEY_PUBLIC_KEY: str | None = os.environ.get("API_KEY_PUBLIC_KEY")  # PEM for RS*/ES*

    # Session Management Configuration
    INACTIVITY_TIMEOUT_MINUTES: int = int(os.environ.get("SESSION_INACTIVITY_TIMEOUT_MINUTES", "180"))
    ACTIVITY_CHECK_INTERVAL_MINUTES: int = int(os.environ.get("ACTIVITY_CHECK_INTERVAL_MINUTES", "10"))
    SESSION_EXTENSION_MINUTES: int = int(os.environ.get("SESSION_EXTENSION_MINUTES", "180"))

    # 32-bytes key for HMAC operations (e.g., CSRF token)
    SECURITY_KEY: str = secrets.token_urlsafe(32)

    # Password security
    PASSWORD_MIN_LENGTH: int = 9
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24

    # OPA (Open Policy Agent) Configuration for Authorization
    OPA_URL: str = os.environ.get("OPA_URL", "http://localhost:8181/v1/data/rbac/allow")
    OPA_ENABLED: bool = os.environ.get("OPA_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    OPA_TIMEOUT: float = float(os.environ.get("OPA_TIMEOUT", "5.0"))

    # Rate limiting - More restrictive for security
    # Can be overridden via environment variables for testing
    RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "10"))
    RATE_LIMIT_LOGIN_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_LOGIN_PER_MINUTE", "5"))
    RATE_LIMIT_PASSWORD_RESET_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_PASSWORD_RESET_PER_MINUTE", "3"))

    # MFA - Authenticator App
    MFA_ISSUER: str = os.environ.get("BRANDING_NAME", "ElevAIte")
    MFA_ENABLED: bool = True

    # MFA - Email
    EMAIL_MFA_GRACE_PERIOD_DAYS: int = int(os.environ.get("EMAIL_MFA_GRACE_PERIOD_DAYS", "30"))

    # MFA Auto-Enable Configuration
    # Specifies which MFA method to auto-enable after grace period expires
    # Options: "email", "sms", "totp", "none"
    MFA_AUTO_ENABLE_METHOD: str = os.environ.get("MFA_AUTO_ENABLE_METHOD", "email")

    # MFA Device Bypass Configuration
    MFA_DEVICE_BYPASS_HOURS: int = int(os.environ.get("MFA_DEVICE_BYPASS_HOURS", "24"))

    # MFA Email Theme Configuration
    MFA_EMAIL_PRIMARY_COLOR: str = os.environ.get("MFA_EMAIL_PRIMARY_COLOR", "e75f33")

    # Branding Configuration
    BRANDING_NAME: str = os.environ.get("BRANDING_NAME", "ElevAIte")
    BRANDING_ORG: str = os.environ.get("BRANDING_ORG", "ElevAIte")
    BRANDING_SUPPORT_EMAIL: str = os.environ.get("BRANDING_SUPPORT_EMAIL", "ElevAIte").lower()

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = []

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Trusted hosts
    ALLOWED_HOSTS: Union[str, List[str]] = ["localhost", "127.0.0.1"]

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

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

    # Email settings for SMTP
    SMTP_TLS: bool = os.environ.get("SMTP_TLS", "True").lower() in ("true", "1", "t")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))  # Default to port 587 (TLS)
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "")
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: str = os.environ.get("EMAILS_FROM_EMAIL", "")
    EMAILS_FROM_NAME: str = os.environ.get("EMAILS_FROM_NAME", "")

    # AWS Configuration for SMS
    AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
    SMS_SENDER_ID: str = os.environ.get("SMS_SENDER_ID", "")

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, list):
            return v
        raise ValueError("CORS_ORIGINS should be a comma-separated string or a list")

    # Redis Settings
    REDIS_ENABLED: bool = os.environ.get("REDIS_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    REDIS_HOST: Optional[str] = os.environ.get("REDIS_HOST")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.environ.get("REDIS_DB", "0"))
    REDIS_USERNAME: Optional[str] = os.environ.get("REDIS_USERNAME")
    REDIS_PASSWORD: Optional[str] = os.environ.get("REDIS_PASSWORD")
    REDIS_SOCKET_TIMEOUT: int = int(os.environ.get("REDIS_SOCKET_TIMEOUT", "5"))
    REDIS_CONNECT_TIMEOUT: int = int(os.environ.get("REDIS_CONNECT_TIMEOUT", "5"))
    # Redis Debounce Settings
    REDIS_DEBOUNCE_SECONDS: int = int(os.environ.get("REDIS_DEBOUNCE_SECONDS", "60"))


settings = Settings()
