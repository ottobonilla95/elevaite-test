"""Authentication routes."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

# No security imports needed here as they're imported from app.core.security
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as async_select

from app.core.config import settings
from app.core.security import get_password_hash, oauth2_scheme, verify_token, get_current_user
from app.db.activity_log import log_user_activity
from app.db.orm import get_async_session
from app.db.models import Session, User
from app.schemas.user import (
    EmailVerificationRequest,
    LoginRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    SessionInfo,
    Token,
    UserCreate,
    UserResponse,
    UserDetail,
)
from app.services.auth_orm import (
    activate_mfa,
    authenticate_user,
    create_user,
    create_user_session,
    invalidate_session,
    setup_mfa,
    verify_refresh_token,
)

router = APIRouter()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=UserDetail)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def register_user(request: Request, user_data: UserCreate, session: AsyncSession = Depends(get_async_session)):
    """Register a new user."""
    user = await create_user(session, user_data)
    return user


@router.post("/login", response_model=Token)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def login(request: Request, login_data: LoginRequest, session: AsyncSession = Depends(get_async_session)):
    """Login with email and password."""
    # Print debug information
    print(f"Login attempt for email: {login_data.email}")

    # Check if user exists
    from app.services.auth_orm import get_user_by_email

    user_check = await get_user_by_email(session, login_data.email)
    if not user_check:
        print(f"User not found: {login_data.email}")
    else:
        print(f"User found: {user_check.email}, status: {user_check.status}, verified: {user_check.is_verified}")

    # Attempt authentication
    user = await authenticate_user(session, login_data.email, login_data.password, login_data.totp_code)

    if not user:
        print(f"Authentication failed for: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user ID as a plain integer
    user_dict = dict(user.__dict__)
    user_id_value = user_dict["id"]
    access_token, refresh_token = await create_user_session(session, user_id_value, request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: RefreshTokenRequest, request: Request, session: AsyncSession = Depends(get_async_session)):
    """Refresh access token using refresh token."""
    user_id = await verify_refresh_token(session, token_data.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Invalidate old refresh token
    await invalidate_session(session, token_data.refresh_token)

    # Create new tokens
    access_token, refresh_token = await create_user_session(session, user_id, request)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(token_data: RefreshTokenRequest, request: Request, session: AsyncSession = Depends(get_async_session)):
    """Logout by invalidating the refresh token."""
    # Validate token first
    user_id = await verify_refresh_token(session, token_data.refresh_token)

    if user_id:
        # Log activity
        await log_user_activity(
            session,
            user_id,
            "logout",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    # Always invalidate the token, even if it's not valid
    await invalidate_session(session, token_data.refresh_token)

    return {"message": "Successfully logged out"}


@router.post("/verify-email")
async def verify_email(verification_data: EmailVerificationRequest, session: AsyncSession = Depends(get_async_session)):
    """Verify user email with token."""
    # Find user with this verification token
    result = await session.execute(async_select(User).where(User.verification_token == verification_data.token))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    # Mark user as verified and active
    stmt = update(User).where(User.id == user.id).values(is_verified=True, status="active", verification_token=None)
    await session.execute(stmt)
    await session.commit()

    # Log activity
    # Get the user ID as a plain integer
    user_dict = dict(user.__dict__)
    user_id_value = user_dict["id"]
    await log_user_activity(session, user_id_value, "email_verified")

    return {"message": "Email successfully verified"}


@router.post("/forgot-password")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def forgot_password(
    request: Request, reset_data: PasswordResetRequest, session: AsyncSession = Depends(get_async_session)
):
    """Initialize password reset flow."""
    # Find user by email
    result = await session.execute(async_select(User).where(User.email == reset_data.email))
    user = result.scalars().first()

    # Always return success even if email doesn't exist (security)
    if not user:
        return {"message": "If your email is registered, you will receive a password reset link"}

    # Generate reset token and expiration
    reset_token = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

    # Store token in database
    stmt = update(User).where(User.id == user.id).values(password_reset_token=reset_token, password_reset_expires=expires)
    await session.execute(stmt)
    await session.commit()

    # TODO: Send password reset email

    # Log activity
    # Get the user ID as a plain integer
    user_dict = dict(user.__dict__)
    user_id_value = user_dict["id"]
    await log_user_activity(
        session,
        user_id_value,
        "password_reset_requested",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"message": "If your email is registered, you will receive a password reset link"}


@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm, session: AsyncSession = Depends(get_async_session)):
    """Reset password with token."""
    # Find user with this reset token
    result = await session.execute(
        async_select(User).where(
            and_(
                User.password_reset_token == reset_data.token,
                User.password_reset_expires > datetime.now(timezone.utc),
            )
        )
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    # Update password
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(
            hashed_password=get_password_hash(reset_data.new_password), password_reset_token=None, password_reset_expires=None
        )
    )
    await session.execute(stmt)

    # Invalidate all sessions
    stmt = update(Session).where(Session.user_id == user.id).values(is_active=False)
    await session.execute(stmt)

    await session.commit()

    # Log activity
    # Get the user ID as a plain integer
    user_dict = dict(user.__dict__)
    user_id_value = user_dict["id"]
    await log_user_activity(session, user_id_value, "password_reset_completed")

    return {"message": "Password successfully reset"}


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa_endpoint(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)):
    """Set up MFA for a user."""
    # Verify token
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])

    # Set up MFA
    secret, uri = await setup_mfa(session, user_id)

    return {
        "secret": secret,
        "qr_code_uri": uri,
    }


@router.post("/mfa/activate")
async def activate_mfa_endpoint(
    data: MfaVerifyRequest, token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)
):
    """Activate MFA after verification."""
    # Verify token
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])

    # Activate MFA
    result = await activate_mfa(session, user_id, data.totp_code)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code",
        )

    return {"message": "MFA successfully activated"}


@router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions(
    request: Request, token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)
):
    """Get all active sessions for the current user."""
    # Verify token
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])

    # Get all active sessions
    result = await session.execute(
        async_select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.is_active.is_(True),
                Session.expires_at > datetime.now(timezone.utc),
            )
        )
    )
    sessions = result.scalars().all()

    # Format sessions
    result = []
    for user_session in sessions:
        # Check if this is the current session
        is_current = False

        # Try to find this session by looking at the User-Agent
        if str(user_session.user_agent) == request.headers.get("user-agent"):
            is_current = True

        session_info = {
            "id": user_session.id,
            "ip_address": user_session.ip_address,
            "user_agent": user_session.user_agent,
            "created_at": user_session.created_at,
            "expires_at": user_session.expires_at,
            "is_current": is_current,
        }
        result.append(session_info)

    return result


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int, token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)
):
    """Revoke a specific session."""
    # Verify token
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])

    # Find session
    result = await session.execute(
        async_select(Session).where(
            and_(
                Session.id == session_id,
                Session.user_id == user_id,
            )
        )
    )
    user_session = result.scalars().first()

    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Revoke session
    stmt = update(Session).where(Session.id == session_id).values(is_active=False)
    await session.execute(stmt)
    await session.commit()

    # Log activity
    await log_user_activity(session, user_id, "session_revoked")

    return {"message": "Session successfully revoked"}
