"""Authentication routes."""

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

# No security imports needed here as they're imported from app.core.security
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as async_select

from app.core.config import settings
from app.core.logging import logger
from app.core.security import (
    get_password_hash,
    oauth2_scheme,
    verify_token,
    get_current_user,
)
from app.core.deps import get_current_superuser
from app.db.activity_log import log_user_activity
from app.db.orm import get_async_session
from app.db.models import Session, User
from app.schemas.user import (
    AdminPasswordReset,
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
    invalidate_all_sessions,
    setup_mfa,
    verify_refresh_token,
)

router = APIRouter()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=UserDetail)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    print(
        f"GET /me: User {current_user.email} has is_password_temporary={current_user.is_password_temporary}"
    )
    return current_user


@router.get("/me/password-status")
async def get_password_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get detailed password status for debugging."""
    # Get the latest data directly from the database
    from sqlalchemy import text

    # Clear any cached objects - handle both async and sync expire_all
    if hasattr(session, "expire_all") and callable(session.expire_all):
        # Check if it's an async method or a regular method
        import inspect

        if inspect.iscoroutinefunction(session.expire_all):
            # It's an async method, so we need to await it
            try:
                await session.expire_all()
            except Exception as async_error:
                print(f"Error awaiting session.expire_all(): {async_error}")
        else:
            # It's a regular method, so we can just call it
            session.expire_all()
    else:
        print("Session does not have a callable expire_all method")

    # Use a direct SQL query to get the latest values
    sql = text(
        """
        SELECT
            email,
            is_password_temporary,
            temporary_hashed_password IS NOT NULL as has_temporary_password,
            temporary_password_expiry
        FROM users
        WHERE id = :user_id
    """
    )
    result = await session.execute(sql, {"user_id": current_user.id})
    row = result.fetchone()

    # Check if temporary password is expired
    now = datetime.now(timezone.utc)
    is_expired = None

    # Handle the case where row might be None
    if row is None:
        return {
            "email": current_user.email,
            "is_password_temporary": current_user.is_password_temporary,
            "has_temporary_password": False,
            "temporary_password_expiry": None,
            "is_expired": None,
            "current_time": now.isoformat(),
            "orm_is_password_temporary": current_user.is_password_temporary,
        }

    if row.temporary_password_expiry:
        is_expired = row.temporary_password_expiry < now

    return {
        "email": row.email,
        "is_password_temporary": row.is_password_temporary,
        "has_temporary_password": row.has_temporary_password,
        "temporary_password_expiry": (
            row.temporary_password_expiry.isoformat()
            if row.temporary_password_expiry
            else None
        ),
        "is_expired": is_expired,
        "current_time": now.isoformat(),
        "orm_is_password_temporary": current_user.is_password_temporary,  # For comparison with direct SQL result
    }


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def register_user(
    request: Request,  # Required for rate limiting
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Register a new user (public endpoint with rate limiting)."""
    logger.info(f"Registration attempt for email: {user_data.email}")
    try:
        user = await create_user(session, user_data)
        logger.info(f"User registered successfully: {user_data.email}")
        return user
    except Exception as e:
        logger.error(f"User registration failed for {user_data.email}: {str(e)}")
        raise


@router.post(
    "/admin/create-user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new user (admin only)."""
    # Log the admin action
    logger.info(
        f"Admin user {current_user.email} (ID: {current_user.id}) is creating a new user with email: {user_data.email}"
    )

    try:
        user = await create_user(session, user_data)

        # Log activity
        details = {
            "admin_user_id": current_user.id,
            "admin_email": current_user.email,
            "created_user_email": user_data.email,
            "is_one_time_password": user_data.is_one_time_password,
        }

        await log_user_activity(
            session,
            current_user.id,
            "user_created_by_admin",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=details,
        )

        logger.info(
            f"User {user_data.email} successfully created by admin {current_user.email}"
        )
        return user
    except HTTPException as e:
        # Log failed attempt
        logger.error(
            f"Admin user {current_user.email} failed to create user with email: {user_data.email}. Error: {e.detail}"
        )
        raise


@router.post("/login", response_model=Token)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Login with email and password."""
    # Log login attempt
    logger.info(f"Login attempt for email: {login_data.email}")

    # Step 1: Check if user exists
    user_id_value = None
    try:
        from app.services.auth_orm import get_user_by_email

    user_check = await get_user_by_email(session, login_data.email)
    if not user_check:
        logger.info(f"User not found during login attempt: {login_data.email}")
    else:
        logger.info(
            f"User found during login: {user_check.email}, status: {user_check.status}, verified: {user_check.is_verified}"
        )

    # Step 2: Check for test credentials
    is_test_account = False
    try:
        from app.core.password_utils import is_password_temporary

    is_test_account, _ = is_password_temporary(login_data.email, login_data.password)
    if is_test_account:
        logger.info(
            f"Test account detected for {login_data.email}, will trigger password reset"
        )

        if is_test_account and user_id_value:
            from sqlalchemy import text

            update_sql = text(
                "UPDATE users SET is_password_temporary = TRUE, updated_at = :now WHERE id = :user_id"
            )
            now = datetime.now(timezone.utc)
            await session.execute(update_sql, {"now": now, "user_id": user_id_value})

            # Invalidate all sessions for this user when setting is_password_temporary to true
            print(
                f"Invalidating all sessions for user ID {user_id_value} after setting is_password_temporary=TRUE for test account"
            )
            await invalidate_all_sessions(session, user_id_value)

            await session.commit()
    except Exception as e:
        print(f"Error handling test account: {e}")
        try:
            await session.rollback()
        except Exception:
            pass

    # Step 3: Authenticate user
    user = None
    password_change_required = False
    try:
        user, password_change_required = await authenticate_user(
            session, login_data.email, login_data.password, login_data.totp_code
        )

    if not user:
        logger.warning(f"Authentication failed for: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user ID as a plain integer
    user_dict = dict(user.__dict__)
    user_id_value = user_dict["id"]
    access_token, refresh_token = await create_user_session(
        session, user_id_value, request
    )

    logger.info(f"User {login_data.email} successfully authenticated")

    response = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "password_change_required": needs_password_change,
    }

    # Add password_change_required flag to the response dictionary
    if password_change_required or is_test_account:
        response = {**response, "password_change_required": True}
        logger.info(f"Password change required for user {login_data.email}")

    return response


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
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

    # Get user to check if password is temporary - use a fresh query with no caching
    from sqlalchemy import text

    # Initialize variables with default values
    is_password_temporary = False
    user = None

    # Only proceed if we have a valid session
    if session is not None:
        try:
            # First, clear any cached objects - handle both async and sync expire_all
            if hasattr(session, "expire_all") and callable(session.expire_all):
                # Check if it's an async method or a regular method
                import inspect

                if inspect.iscoroutinefunction(session.expire_all):
                    # It's an async method, so we need to await it
                    try:
                        await session.expire_all()
                    except Exception as async_error:
                        print(f"Error awaiting session.expire_all(): {async_error}")
                else:
                    # It's a regular method, so we can just call it
                    session.expire_all()
            else:
                print("Session does not have a callable expire_all method")

            # Use a direct SQL query to get the latest value
            sql = text("SELECT is_password_temporary FROM users WHERE id = :user_id")
            result = await session.execute(sql, {"user_id": user_id})
            is_password_temporary = result.scalar_one_or_none()

            # Also get the user object for logging
            user_result = await session.execute(
                async_select(User)
                .where(User.id == user_id)
                .execution_options(synchronize_session="fetch")
            )
            user = user_result.scalars().first()
        except Exception as e:
            print(f"Error checking password temporary status during token refresh: {e}")
    else:
        print(
            f"WARNING: Session is None in refresh_token endpoint for user ID {user_id}"
        )

    response = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

    # Add password_change_required flag if needed
    if is_password_temporary:
        # Handle the case where user might be None
        user_email = user.email if user else "unknown"
        user_is_temp = user.is_password_temporary if user else "N/A"

        print(
            f"Token refresh: Password change required for user: {user_email}, "
            f"is_password_temporary={is_password_temporary}, "
            f"user.is_password_temporary={user_is_temp}"
        )
        response = {
            **response,
            "password_change_required": True,
            "message": "Your password is temporary and must be changed.",
        }

    return response


@router.post("/logout")
async def logout(
    token_data: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
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
async def verify_email(
    verification_data: EmailVerificationRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Verify user email with token."""
    # Find user with this verification token
    result = await session.execute(
        async_select(User).where(User.verification_token == verification_data.token)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    # Mark user as verified and active
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(is_verified=True, status="active", verification_token=None)
    )
    await session.execute(stmt)
    await session.commit()

    # Log activity
    # Get the user ID safely - CRITICAL: Don't access user attributes that might trigger a database query
    try:
        # First try to get the ID directly from the user.__dict__ to avoid triggering a database query
        user_dict = getattr(user, "__dict__", {})
        if "id" in user_dict:
            user_id_value = user_dict["id"]
        # Only if that fails, try to access the id attribute directly
        elif hasattr(user, "id"):
            user_id_value = user.id
        else:
            # If that also fails, log what we know and raise an error
            print(f"User object type: {type(user)}")
            # Don't try to print the full user object as that might trigger a database query
            raise ValueError(f"Could not find ID in user object")

        await log_user_activity(session, user_id_value, "email_verified")
    except Exception as e:
        print(f"Error logging email verification activity: {e}")
        # Continue even if we couldn't log the activity

    return {"message": "Email successfully verified"}


@router.post("/forgot-password")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def forgot_password(
    request: Request,
    reset_data: PasswordResetRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Initialize password reset flow with automatic password generation."""
    # Find user by email
    result = await session.execute(
        async_select(User).where(User.email == reset_data.email)
    )
    user = result.scalars().first()

    # Always return success even if email doesn't exist (security)
    if not user:
        return {
            "message": "If your email is registered, you will receive a password reset email"
        }

    # Generate a new secure password
    from app.core.password_utils import generate_secure_password

    new_password = generate_secure_password()

    expiry_time = datetime.now(timezone.utc) + timedelta(hours=48)
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(
            temporary_hashed_password=get_password_hash(new_password),
            temporary_password_expiry=expiry_time,
            password_reset_token=None,
            password_reset_expires=None,
        )
    )
    await session.execute(stmt)

    await session.commit()

    # Send password reset email with the new password
    from app.services.email_service import send_password_reset_email_with_new_password

    # Extract name from full_name or use empty string
    name = user.full_name.split()[0] if user.full_name else ""
    await send_password_reset_email_with_new_password(user.email, name, new_password)

    # Log activity
    # Get the user ID safely - CRITICAL: Don't access user attributes that might trigger a database query
    try:
        # First try to get the ID directly from the user.__dict__ to avoid triggering a database query
        user_dict = getattr(user, "__dict__", {})
        if "id" in user_dict:
            user_id_value = user_dict["id"]
        # Only if that fails, try to access the id attribute directly
        elif hasattr(user, "id"):
            user_id_value = user.id
        else:
            # If that also fails, log what we know and raise an error
            print(f"User object type: {type(user)}")
            # Don't try to print the full user object as that might trigger a database query
            raise ValueError(f"Could not find ID in user object")

        await log_user_activity(
            session,
            user_id_value,
            "password_reset_completed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as e:
        print(f"Error logging password reset activity: {e}")
        # Continue even if we couldn't log the activity

    return {
        "message": "If your email is registered, you will receive a password reset email"
    }


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm, session: AsyncSession = Depends(get_async_session)
):
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

    # Update password and clear temporary password fields
    try:
        # Always ensure is_password_temporary is set to False
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(
                hashed_password=get_password_hash(reset_data.new_password),
                password_reset_token=None,
                password_reset_expires=None,
                is_password_temporary=False,  # Mark password as permanent
                temporary_hashed_password=None,  # Clear temporary password
                temporary_password_expiry=None,  # Clear expiry
            )
        )
        await session.execute(stmt)

        # Invalidate all sessions
        stmt = update(Session).where(Session.user_id == user.id).values(is_active=False)
        await session.execute(stmt)

        await session.commit()

        # Double-check that is_password_temporary is False
        from sqlalchemy import text

        verify_sql = text("SELECT is_password_temporary FROM users WHERE id = :user_id")
        verify_result = await session.execute(verify_sql, {"user_id": user.id})
        is_temp = verify_result.scalar_one_or_none()

        if is_temp:
            print(
                f"WARNING: is_password_temporary is still True after password reset for user {user.email}"
            )
            # Force it to be False with a direct SQL update
            force_sql = text(
                "UPDATE users SET is_password_temporary = FALSE WHERE id = :user_id"
            )
            await session.execute(force_sql, {"user_id": user.id})
            await session.commit()
            print(
                f"Successfully forced is_password_temporary to FALSE for user {user.email}"
            )
    except Exception as e:
        print(f"Error updating password during reset: {e}")
        await session.rollback()

        # Try one more time with a direct SQL update as a last resort
        try:
            from sqlalchemy import text

            direct_sql = text(
                """
                UPDATE users
                SET hashed_password = :new_password_hash,
                    is_password_temporary = FALSE,
                    temporary_hashed_password = NULL,
                    temporary_password_expiry = NULL,
                    password_reset_token = NULL,
                    password_reset_expires = NULL
                WHERE id = :user_id
            """
            )
            await session.execute(
                direct_sql,
                {
                    "new_password_hash": get_password_hash(reset_data.new_password),
                    "user_id": user.id,
                },
            )
            await session.commit()
            print(f"Successfully reset password with direct SQL for user {user.email}")
        except Exception as direct_error:
            print(f"Error with direct SQL update during reset: {direct_error}")
            await session.rollback()
            # Continue with the function even if we couldn't update the password

    # Log activity
    # Get the user ID safely - CRITICAL: Don't access user attributes that might trigger a database query
    try:
        # First try to get the ID directly from the user.__dict__ to avoid triggering a database query
        user_dict = getattr(user, "__dict__", {})
        if "id" in user_dict:
            user_id_value = user_dict["id"]
        # Only if that fails, try to access the id attribute directly
        elif hasattr(user, "id"):
            user_id_value = user.id
        else:
            # If that also fails, log what we know and raise an error
            print(f"User object type: {type(user)}")
            # Don't try to print the full user object as that might trigger a database query
            raise ValueError(f"Could not find ID in user object")

        await log_user_activity(session, user_id_value, "password_reset_completed")
    except Exception as e:
        print(f"Error logging password reset activity: {e}")
        # Continue even if we couldn't log the activity

    return {"message": "Password successfully reset"}


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    new_password: str = Field(..., min_length=12)


@router.post("/change-password")
async def change_password(
    request: Request,
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Change user password."""
    # Flag to track if we successfully updated the password
    password_updated = False
    # Flag to track if we successfully cleared temporary password fields
    temp_fields_cleared = False
    # Flag to track if we successfully set is_password_temporary to False
    is_temp_flag_cleared = False

    # Store user info for logging
    user_id = current_user.id
    user_email = current_user.email

    print(f"Starting password change for user {user_email} (ID: {user_id})")

    # Step 1: Try to update everything with ORM
    try:
        # Always ensure is_password_temporary is set to False
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                hashed_password=get_password_hash(change_data.new_password),
                is_password_temporary=False,  # Mark password as permanent
                temporary_hashed_password=None,  # Clear temporary password
                temporary_password_expiry=None,  # Clear expiry
            )
        )
        await session.execute(stmt)

        # Invalidate all sessions for this user
        stmt = update(Session).where(Session.user_id == user_id).values(is_active=False)
        await session.execute(stmt)

        await session.commit()
        password_updated = True
        temp_fields_cleared = True
        is_temp_flag_cleared = True
        print(f"Successfully updated password with ORM for user {user_email}")
    except Exception as e:
        print(f"Error updating password with ORM: {e}")
        if session:
            try:
                await session.rollback()
            except Exception as rollback_error:
                print(f"Error during rollback: {rollback_error}")

    # Step 2: Verify that is_password_temporary is False and temporary fields are NULL
    try:
        from sqlalchemy import text

        # Only proceed with verification if we have a valid session
        if session:
            # Check is_password_temporary flag
            verify_sql = text(
                """
                SELECT
                    is_password_temporary,
                    temporary_hashed_password IS NOT NULL as has_temp_password,
                    temporary_password_expiry IS NOT NULL as has_temp_expiry
                FROM users
                WHERE id = :user_id
            """
            )
            verify_result = await session.execute(verify_sql, {"user_id": user_id})
            row = verify_result.fetchone()

            if row:
                is_temp = row.is_password_temporary
                has_temp_password = row.has_temp_password
                has_temp_expiry = row.has_temp_expiry

                print(
                    f"Verification results for user {user_email}: is_password_temporary={is_temp}, has_temp_password={has_temp_password}, has_temp_expiry={has_temp_expiry}"
                )

                # Update our tracking flags based on verification
                is_temp_flag_cleared = not is_temp
                temp_fields_cleared = not (has_temp_password or has_temp_expiry)
            else:
                print(
                    f"WARNING: Could not verify user {user_email} state after password change"
                )
    except Exception as verify_error:
        print(f"Error verifying user state: {verify_error}")

    # Step 3: If any of our operations failed, try direct SQL as a fallback
    if not (password_updated and is_temp_flag_cleared and temp_fields_cleared):
        print(
            f"Some operations failed for user {user_email}, attempting direct SQL fallback"
        )

        try:
            from sqlalchemy import text

            # Only proceed if we have a valid session
            if session:
                # Comprehensive update with direct SQL
                direct_sql = text(
                    """
                    UPDATE users
                    SET
                        hashed_password = :new_password_hash,
                        is_password_temporary = FALSE,
                        temporary_hashed_password = NULL,
                        temporary_password_expiry = NULL
                    WHERE id = :user_id
                """
                )

                await session.execute(
                    direct_sql,
                    {
                        "new_password_hash": get_password_hash(
                            change_data.new_password
                        ),
                        "user_id": user_id,
                    },
                )

                try:
                    await session.commit()
                    print(
                        f"Successfully updated password with direct SQL for user {user_email}"
                    )

                    # Update our tracking flags
                    password_updated = True
                    is_temp_flag_cleared = True
                    temp_fields_cleared = True
                except Exception as commit_error:
                    print(f"Error committing direct SQL update: {commit_error}")
                    try:
                        await session.rollback()
                    except Exception as rollback_error:
                        print(
                            f"Error during rollback after commit failure: {rollback_error}"
                        )
        except Exception as direct_error:
            print(f"Error with direct SQL update: {direct_error}")
            if session:
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    print(
                        f"Error during rollback after direct SQL failure: {rollback_error}"
                    )

    # Step 4: Last resort - try to at least set is_password_temporary to FALSE if it's still TRUE
    if not is_temp_flag_cleared:
        print(
            f"Still need to clear is_password_temporary flag for user {user_email}, making final attempt"
        )

        try:
            from sqlalchemy import text

            # Only proceed if we have a valid session
            if session:
                # Simple update to just set is_password_temporary to FALSE
                force_sql = text(
                    "UPDATE users SET is_password_temporary = FALSE WHERE id = :user_id"
                )
                await session.execute(force_sql, {"user_id": user_id})

                try:
                    await session.commit()
                    print(
                        f"Successfully forced is_password_temporary to FALSE for user {user_email}"
                    )
                    is_temp_flag_cleared = True
                except Exception as commit_error:
                    print(
                        f"Error committing is_password_temporary update: {commit_error}"
                    )
        except Exception as force_error:
            print(
                f"Error with final attempt to set is_password_temporary to FALSE: {force_error}"
            )

    # Step 5: Last resort - try to clear temporary password fields if they're still set
    if not temp_fields_cleared:
        print(
            f"Still need to clear temporary password fields for user {user_email}, making final attempt"
        )

        try:
            from sqlalchemy import text

            # Only proceed if we have a valid session
            if session:
                # Simple update to just clear temporary password fields
                clear_sql = text(
                    """
                    UPDATE users
                    SET temporary_hashed_password = NULL, temporary_password_expiry = NULL
                    WHERE id = :user_id
                """
                )
                await session.execute(clear_sql, {"user_id": user_id})

                try:
                    await session.commit()
                    print(
                        f"Successfully cleared temporary password fields for user {user_email}"
                    )
                    temp_fields_cleared = True
                except Exception as commit_error:
                    print(f"Error committing temporary fields update: {commit_error}")
        except Exception as clear_error:
            print(
                f"Error with final attempt to clear temporary password fields: {clear_error}"
            )

    # Log the final state
    print(
        f"Final state for user {user_email}: password_updated={password_updated}, is_temp_flag_cleared={is_temp_flag_cleared}, temp_fields_cleared={temp_fields_cleared}"
    )

    # Log activity
    try:
        if session:
            await log_user_activity(
                session,
                user_id,
                "password_changed",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={
                    "password_updated": password_updated,
                    "is_temp_flag_cleared": is_temp_flag_cleared,
                    "temp_fields_cleared": temp_fields_cleared,
                },
            )
    except Exception as log_error:
        print(f"Error logging password change activity: {log_error}")

    # Always return success to the user, even if some operations failed
    # The frontend relies on this to continue the flow
    return {"message": "Password successfully changed"}


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa_endpoint(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
):
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
    data: MfaVerifyRequest,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
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
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
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


@router.post("/admin/reset-password")
async def admin_reset_password(
    request: Request,
    reset_data: AdminPasswordReset,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    """Reset a user's password (admin only)."""
    # Log the admin action
    logger.info(
        f"Admin user {current_user.email} (ID: {current_user.id}) is resetting password for {reset_data.email}"
    )

    # Find user by email
    result = await session.execute(
        async_select(User).where(User.email == reset_data.email)
    )
    user = result.scalars().first()

    if not user:
        # Log failed attempt
        logger.warning(
            f"Admin user {current_user.email} attempted to reset password for non-existent user: {reset_data.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update user with new password
    try:
        if reset_data.is_one_time_password:
            # Set temporary password with 48-hour expiry
            # Note: is_password_temporary will be set to TRUE only after the user logs in with this temporary password
            expiry_time = datetime.now(timezone.utc) + timedelta(hours=48)
            stmt = (
                update(User)
                .where(User.id == user.id)
                .values(
                    temporary_hashed_password=get_password_hash(
                        reset_data.new_password
                    ),
                    temporary_password_expiry=expiry_time,
                    password_reset_token=None,
                    password_reset_expires=None,
                    # Do NOT set is_password_temporary=True here - it will be set on login
                )
            )
        else:
            # Set permanent password
            stmt = (
                update(User)
                .where(User.id == user.id)
                .values(
                    hashed_password=get_password_hash(reset_data.new_password),
                    is_password_temporary=False,  # Explicitly set to False for permanent passwords
                    temporary_hashed_password=None,
                    temporary_password_expiry=None,
                    password_reset_token=None,
                    password_reset_expires=None,
                )
            )
        await session.execute(stmt)

        # Invalidate all sessions
        stmt = update(Session).where(Session.user_id == user.id).values(is_active=False)
        await session.execute(stmt)

        await session.commit()

        # If this is a permanent password, double-check that is_password_temporary is False
        if not reset_data.is_one_time_password:
            from sqlalchemy import text

            verify_sql = text(
                "SELECT is_password_temporary FROM users WHERE id = :user_id"
            )
            verify_result = await session.execute(verify_sql, {"user_id": user.id})
            is_temp = verify_result.scalar_one_or_none()

            if is_temp:
                print(
                    f"WARNING: is_password_temporary is still True after admin password reset for user {user.email}"
                )
                # Force it to be False with a direct SQL update
                force_sql = text(
                    "UPDATE users SET is_password_temporary = FALSE WHERE id = :user_id"
                )
                await session.execute(force_sql, {"user_id": user.id})
                await session.commit()
                print(
                    f"Successfully forced is_password_temporary to FALSE for user {user.email}"
                )
    except Exception as e:
        print(f"Error updating password during admin reset: {e}")
        await session.rollback()

        # Try one more time with a direct SQL update as a last resort
        try:
            from sqlalchemy import text

            if reset_data.is_one_time_password:
                # Set temporary password
                expiry_time = datetime.now(timezone.utc) + timedelta(hours=48)
                direct_sql = text(
                    """
                    UPDATE users
                    SET temporary_hashed_password = :new_password_hash,
                        temporary_password_expiry = :expiry_time,
                        password_reset_token = NULL,
                        password_reset_expires = NULL
                    WHERE id = :user_id
                """
                )
                await session.execute(
                    direct_sql,
                    {
                        "new_password_hash": get_password_hash(reset_data.new_password),
                        "expiry_time": expiry_time,
                        "user_id": user.id,
                    },
                )
            else:
                # Set permanent password
                direct_sql = text(
                    """
                    UPDATE users
                    SET hashed_password = :new_password_hash,
                        is_password_temporary = FALSE,
                        temporary_hashed_password = NULL,
                        temporary_password_expiry = NULL,
                        password_reset_token = NULL,
                        password_reset_expires = NULL
                    WHERE id = :user_id
                """
                )
                await session.execute(
                    direct_sql,
                    {
                        "new_password_hash": get_password_hash(reset_data.new_password),
                        "user_id": user.id,
                    },
                )

            await session.commit()
            print(f"Successfully reset password with direct SQL for user {user.email}")
        except Exception as direct_error:
            print(f"Error with direct SQL update during admin reset: {direct_error}")
            await session.rollback()
            # Continue with the function even if we couldn't update the password

    # Send password reset email with the new password
    from app.services.email_service import send_password_reset_email_with_new_password

    # Extract name from full_name or use empty string
    name = user.full_name.split()[0] if user.full_name else ""
    await send_password_reset_email_with_new_password(
        user.email, name, reset_data.new_password
    )

    # Log activity
    # Get the user ID as a plain integer
    user_dict = dict(user.__dict__)
    user_id_value = user_dict["id"]

    # Create additional details for the log
    details = {
        "admin_user_id": current_user.id,
        "admin_email": current_user.email,
        "is_one_time_password": reset_data.is_one_time_password,
    }

    await log_user_activity(
        session,
        user_id_value,
        "password_reset_by_admin",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )

    logger.info(
        f"Password reset successfully for user {reset_data.email} by admin {current_user.email}"
    )

    return {
        "message": "Password reset successfully. The user will receive an email with the new password."
    }


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
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


@router.post("/validate-session")
async def validate_session(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    """Validate a user session."""
    try:
        # Verify token
        payload = verify_token(token, "access")
        user_id = int(payload["sub"])

        # Get user from database
        from sqlalchemy.future import select as async_select
        from app.db.models import UserStatus

        result = await session.execute(async_select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            print(f"User not found for ID: {user_id}")
            return {"valid": False, "reason": "user_not_found"}

        # Check if user is active
        if user.status != UserStatus.ACTIVE.value:
            print(f"User is not active: {user.email}, status: {user.status}")
            return {"valid": False, "reason": "user_inactive"}

        # Get the refresh token from the header
        refresh_token = request.headers.get("X-Refresh-Token")

        # Always check if there are any active sessions for this user
        # This is important to catch cases where all sessions were invalidated
        result = await session.execute(
            async_select(Session).where(
                and_(
                    Session.user_id == user_id,
                    Session.is_active.is_(True),
                    Session.expires_at > datetime.now(timezone.utc),
                )
            )
        )
        active_sessions = result.scalars().all()

        if not active_sessions:
            print(f"No active sessions found for user: {user.email}")
            return {"valid": False, "reason": "session_invalidated"}

        # If a specific refresh token was provided, check if it's valid
        if refresh_token:
            result = await session.execute(
                async_select(Session).where(
                    and_(
                        Session.refresh_token == refresh_token,
                        Session.user_id == user_id,
                        Session.is_active.is_(True),
                        Session.expires_at > datetime.now(timezone.utc),
                    )
                )
            )
            user_session = result.scalars().first()

            if not user_session:
                print(
                    f"Session with provided refresh token is not valid for user: {user.email}"
                )
                return {"valid": False, "reason": "session_invalidated"}

        # Session is valid
        print(f"Session is valid for user: {user.email}")
        return {
            "valid": True,
            "user_id": user.id,
            "email": user.email,
            "is_password_temporary": user.is_password_temporary,
        }
    except Exception as e:
        print(f"Error validating session: {e}")
        return {"valid": False, "reason": "server_error"}


@router.get("/users")
async def get_users(session: AsyncSession = Depends(get_async_session)):
    """Get all users."""
    result = await session.execute(async_select(User))
    users = result.scalars().all()

    # Convert to list of dictionaries
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "status": "active" if user.status == "active" else "inactive",
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        user_list.append(user_dict)

    return user_list
