"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class UserStatus(str, Enum):
    """User status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted" 


# Define timezone-aware datetime functions
def utcnow() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Base mixin with timestamp fields."""

    # Use timezone-aware datetime functions
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=UserStatus.PENDING.value, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    application_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_manager: Mapped[bool] = mapped_column(default=False, nullable=False)

    is_password_temporary: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Contact info
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # 2FA/MFA
    mfa_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # TOTP secret
    sms_mfa_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    email_mfa_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    biometric_mfa_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    email_mfa_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # Current email MFA code for verification
    email_mfa_code_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Email MFA code expiration

    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Temporary password for password reset flow
    temporary_hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    temporary_password_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Email verification
    verification_token: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, nullable=True
    )

    # Last login information
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    activities: Mapped[List["UserActivity"]] = relationship(
        "UserActivity", back_populates="user", cascade="all, delete-orphan"
    )

    biometric_devices: Mapped[List["BiometricDevice"]] = relationship(
       "BiometricDevice", back_populates="user", cascade="all, delete-orphan"
   )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<User {self.email}>"


class Session(Base, TimestampMixin):
    """User session model for tracking active sessions."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    refresh_token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Session {self.id} for User {self.user_id}>"


class MfaDeviceVerification(Base, TimestampMixin):
    """MFA device verification tracking for 24-hour MFA bypass."""

    __tablename__ = "mfa_device_verifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_fingerprint: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    mfa_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'totp', 'sms', 'email'

    # Relationship to User
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        """String representation."""
        return f"<MfaDeviceVerification {self.id} for User {self.user_id}>"


class UserActivity(Base, TimestampMixin):
    """User activity logging model for audit purposes."""

    __tablename__ = "user_activity"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="activities")

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserActivity {self.id} - {self.action} by User {self.user_id}>"

class BiometricDevice(Base, TimestampMixin):
    """Biometric device registration for MFA."""
    
    __tablename__ = "biometric_devices"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Device identification
    device_fingerprint: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        index=True,
        unique=True
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Public key for verification (NOT biometric data!)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status tracking
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Metadata
    ip_address_at_registration: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    user_agent_at_registration: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    
    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="biometric_devices")
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<BiometricDevice {self.id} '{self.device_name}' for User {self.user_id}>"