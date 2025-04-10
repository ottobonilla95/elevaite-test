"""Authentication services using SQLAlchemy ORM."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, TypeVar

from fastapi import HTTPException, Request
from fastapi import status as http_status
from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_totp_secret,
    generate_totp_uri,
    get_password_hash,
    verify_password,
    verify_totp,
)
from app.db.activity_log import log_user_activity

# from app.db.orm import get_async_session  # Uncomment if needed
from app.db.orm_models import Session, User, UserStatus
from app.schemas.user import UserCreate


# Type variable for User model
T = TypeVar("T", bound=User)


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def authenticate_user(
    session: AsyncSession, email: str, password: str, totp_code: Optional[str] = None
) -> Optional[User]:
    """Authenticate a user with email and password."""
    user = await get_user_by_email(session, email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(
                failed_login_attempts=user.failed_login_attempts + 1,
                locked_until=(
                    datetime.now(timezone.utc) + timedelta(minutes=15) if user.failed_login_attempts + 1 >= 5 else None
                ),
            )
        )
        await session.execute(stmt)
        await session.commit()
        return None

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        return None

    # Check if account is active
    if user.status != UserStatus.ACTIVE.value:
        return None

    # Check MFA if enabled
    if user.mfa_enabled and not totp_code:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="TOTP code required",
        )

    if user.mfa_enabled and totp_code and user.mfa_secret and not verify_totp(totp_code, user.mfa_secret):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code",
        )

    # Reset failed login attempts and update last login
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(
            failed_login_attempts=0,
            locked_until=None,
            last_login=datetime.now(timezone.utc),
        )
    )
    await session.execute(stmt)
    await session.commit()

    return user


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user."""
    # Check if user with this email already exists
    existing_user = await get_user_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create verification token
    verification_token = uuid.uuid4()

    # Create user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        status=UserStatus.PENDING.value,
        is_verified=False,
        verification_token=verification_token,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # TODO: Send verification email

    return new_user


async def create_user_session(session: AsyncSession, user_id: int, request: Request) -> Tuple[str, str]:
    """Create a new user session and return tokens."""
    # Create tokens
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # Store session
    new_session = Session(
        user_id=user_id,
        refresh_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    session.add(new_session)
    await session.commit()

    # Log activity
    await log_user_activity(
        user_id,
        "login",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return access_token, refresh_token


async def verify_refresh_token(session: AsyncSession, refresh_token: str) -> Optional[int]:
    """Verify a refresh token and return the user ID."""
    # Find session with this refresh token
    result = await session.execute(
        select(Session).where(
            and_(
                Session.refresh_token == refresh_token,
                Session.expires_at > datetime.now(timezone.utc),
                Session.is_active.is_(True),
            )
        )
    )
    user_session = result.scalars().first()

    if not user_session:
        return None

    # Verify user is active
    result = await session.execute(
        select(User).where(
            and_(
                User.id == user_session.user_id,
                User.status == UserStatus.ACTIVE.value,
            )
        )
    )
    user = result.scalars().first()

    if not user:
        return None

    return user_session.user_id


async def invalidate_session(session: AsyncSession, refresh_token: str) -> bool:
    """Invalidate a user session."""
    stmt = update(Session).where(Session.refresh_token == refresh_token).values(is_active=False)
    await session.execute(stmt)
    await session.commit()
    # For SQLAlchemy 2.0, we need to check if any rows were affected
    return True  # Simplified for now, as rowcount might not be directly accessible


async def setup_mfa(session: AsyncSession, user_id: int) -> Tuple[str, str]:
    """Set up MFA for a user."""
    # Get user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Generate secret
    secret = generate_totp_secret()

    # Store secret
    stmt = update(User).where(User.id == user_id).values(mfa_secret=secret)
    await session.execute(stmt)
    await session.commit()

    # Generate URI for QR code
    uri = generate_totp_uri(secret, user.email)

    return secret, uri


async def activate_mfa(session: AsyncSession, user_id: int, totp_code: str) -> bool:
    """Activate MFA for a user after verification."""
    # Get user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user or not user.mfa_secret:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up",
        )

    # Verify TOTP code
    if not user.mfa_secret or not verify_totp(totp_code, user.mfa_secret):
        return False

    # Activate MFA
    stmt = update(User).where(User.id == user_id).values(mfa_enabled=True)
    await session.execute(stmt)
    await session.commit()

    # Log activity
    await log_user_activity(user_id, "mfa_activated")

    return True
