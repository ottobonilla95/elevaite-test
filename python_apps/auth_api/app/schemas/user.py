"""User schemas."""

import re
from datetime import datetime
from typing import List, Optional, Union, ClassVar
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=12)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")

        # Check for at least one lowercase, one uppercase, one digit, and one special char
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v


class UserUpdate(BaseModel):
    """User update schema."""

    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordUpdate(BaseModel):
    """Password update schema."""

    current_password: str
    new_password: str = Field(..., min_length=12)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")

        # Check for at least one lowercase, one uppercase, one digit, and one special char
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v


class UserResponse(UserBase):
    """User response schema."""

    id: int
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


class UserDetail(UserResponse):
    """Detailed user information schema."""

    status: str
    last_login: Optional[datetime] = None


class Token(BaseModel):
    """Token schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: Optional[Union[int, str]] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str
    new_password: str = Field(..., min_length=12)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")

        # Check for at least one lowercase, one uppercase, one digit, and one special char
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""

    token: UUID


class MfaSetupResponse(BaseModel):
    """MFA setup response schema."""

    secret: str
    qr_code_uri: str


class MfaVerifyRequest(BaseModel):
    """MFA verification request schema."""

    totp_code: str


class SessionInfo(BaseModel):
    """Session information schema."""

    id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    is_current: bool = False

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
