"""Authentication services using SQLAlchemy ORM."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, TypeVar
from app.core.password_utils import is_password_temporary, normalize_email

from fastapi import HTTPException, Request
from fastapi import status as http_status
from sqlalchemy import and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.logging import logger
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
from app.db.models import Session, User, UserStatus
from app.schemas.user import UserCreate


# Type variable for User model
T = TypeVar("T", bound=User)


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email in the current tenant context."""
    # Use the normalize_email helper
    normalized_email = normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized_email))
    return result.scalars().first()


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
    totp_code: Optional[str] = None,
    request: Optional[Request] = None,
) -> Tuple[Optional[User], bool]:
    """
    Authenticate a user with email and password.

    Returns:
        Tuple[Optional[User], bool]: (user, password_change_required)
            - user: The authenticated user or None if authentication failed
            - password_change_required: True if the user needs to change their password
    """
    print(f"Authenticating user: {email}")

    # Check if session is None
    if session is None:
        print(f"WARNING: Session is None in authenticate_user for user {email}")
        return None, False

    # Check for test credentials that should trigger password reset flow
    from app.core.password_utils import is_password_temporary

    # First check for known test accounts
    is_test_account, message = is_password_temporary(email, password)
    temp_password_detected = False

    if is_test_account:
        try:
            # Find the user by email
            user = await get_user_by_email(session, email)
            if user:
                # Check if the user has already changed their password
                # If is_password_temporary is explicitly set to False, respect that
                if user.is_password_temporary is False:
                    print(
                        f"User {email} has already changed their password, not requiring reset"
                    )
                    return user, False
                else:
                    print(f"Test account detected for user {email}: {message}")
                    temp_password_detected = True
                    # Don't return early - continue to check MFA
        except Exception as e:
            print(f"Error checking for test account: {e}")
            # Continue with normal authentication

    try:
        user = await get_user_by_email(session, email)

        if not user:
            print(f"User not found in authenticate_user: {email}")
            return None, False
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None, False

    print(f"Checking password for user: {email}")
    now = datetime.now(timezone.utc)

    try:
        # First check if there's a temporary password and it hasn't expired
        if user.temporary_hashed_password and user.temporary_password_expiry:
            # Check if temporary password is expired
            if user.temporary_password_expiry < now:
                print(f"Temporary password expired for user: {email}")
                try:
                    # Clear expired temporary password
                    stmt = (
                        update(User)
                        .where(User.id == user.id)
                        .values(
                            temporary_hashed_password=None,
                            temporary_password_expiry=None,
                            updated_at=now,
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()
                except Exception as e:
                    print(f"Error clearing expired temporary password: {e}")
                    try:
                        await session.rollback()
                    except Exception as rollback_error:
                        print(f"Error during rollback: {rollback_error}")
            else:
                # Check if the provided password matches the temporary password
                try:
                    if verify_password(password, user.temporary_hashed_password):
                        user_id = user.id
                        user.is_password_temporary = True
                        from sqlalchemy import text

                        # Use raw SQL with explicit schema to avoid any ORM caching issues
                        update_sql = text(
                            """
                            UPDATE users
                            SET temporary_hashed_password = NULL,
                                temporary_password_expiry = NULL,
                                is_password_temporary = TRUE,
                                is_verified = TRUE,
                                updated_at = :now
                            WHERE id = :user_id
                        """
                        )

                        try:
                            result = await session.execute(
                                update_sql, {"now": now, "user_id": user_id}
                            )

                            await session.commit()

                            # Log the SQL result
                            # Use getattr to safely access rowcount which might not exist
                            rowcount = getattr(result, "rowcount", "unknown")
                            print(f"SQL update result: {rowcount} rows affected")

                            # Verify the update with a direct query
                            try:
                                verify_sql = text(
                                    "SELECT is_password_temporary FROM users WHERE id = :user_id"
                                )
                                verify_result = await session.execute(
                                    verify_sql, {"user_id": user_id}
                                )
                                # Use scalar_one_or_none instead of scalar_one to handle no results
                                is_temp = verify_result.scalar_one_or_none()
                                print(
                                    f"Verification query shows is_password_temporary = {is_temp}"
                                )
                            except Exception as verify_error:
                                print(
                                    f"Error verifying is_password_temporary: {verify_error}"
                                )
                                # Default to True if verification fails
                                is_temp = True

                        except Exception as e:
                            print(f"Error updating is_password_temporary: {e}")
                            try:
                                await session.rollback()
                            except Exception as rollback_error:
                                print(f"Error during rollback: {rollback_error}")
                            # Default to True if update fails
                            is_temp = True

                        # Create a new user object with is_password_temporary=True
                        updated_user = user

                        try:
                            # Force a clean refresh of the user object from the database
                            if session:
                                try:
                                    # Check if expire_all is callable before using it
                                    if hasattr(session, "expire_all") and callable(
                                        session.expire_all
                                    ):
                                        # Check if it's an async method or a regular method
                                        import inspect

                                        if inspect.iscoroutinefunction(
                                            session.expire_all
                                        ):
                                            # It's an async method, so we need to await it
                                            try:
                                                await session.expire_all()
                                            except Exception as async_error:
                                                print(
                                                    f"Error awaiting session.expire_all(): {async_error}"
                                                )
                                        else:
                                            # It's a regular method, so we can just call it
                                            session.expire_all()
                                    else:
                                        print(
                                            "Session does not have a callable expire_all method"
                                        )
                                except Exception as expire_error:
                                    print(
                                        f"Error expiring session cache: {expire_error}"
                                    )

                                try:
                                    # Use a fresh connection to get the latest data
                                    result = await session.execute(
                                        text("SELECT * FROM users WHERE id = :user_id"),
                                        {"user_id": user_id},
                                    )
                                    user_data = result.mappings().first()

                                    # Safely access is_password_temporary from user_data
                                    if (
                                        user_data
                                        and "is_password_temporary" in user_data
                                    ):
                                        updated_user.is_password_temporary = user_data[
                                            "is_password_temporary"
                                        ]
                                    else:
                                        # If we can't get the data, force it to True
                                        print(
                                            f"Could not get user data, forcing is_password_temporary=True"
                                        )
                                        updated_user.is_password_temporary = True
                                except Exception as query_error:
                                    print(f"Error querying user data: {query_error}")
                                    # Force it to True if query fails
                                    updated_user.is_password_temporary = True
                            else:
                                print(
                                    f"Session is None, forcing is_password_temporary=True"
                                )
                                updated_user.is_password_temporary = True
                        except Exception as refresh_error:
                            print(f"Error refreshing user data: {refresh_error}")
                            # Force it to True if refresh fails
                            updated_user.is_password_temporary = True

                        # Double-check that the flag was set
                        if not updated_user.is_password_temporary:
                            print(
                                f"WARNING: is_password_temporary flag was not set for user {email} despite SQL update!"
                            )
                            # Force the flag to be True in the returned object even if the DB update failed
                            updated_user.is_password_temporary = True

                        # Log that we're returning with password change required
                        print(
                            f"Temporary password login successful for {email}, is_password_temporary={updated_user.is_password_temporary}"
                        )

                        # CRITICAL: Return password_change_required=True to force the user to change their password
                        # This is the value that will be used in the login endpoint to determine if the user
                        # needs to change their password
                        print(
                            f"Returning password_change_required=True for user {email}"
                        )
                        return updated_user, True
                except Exception as e:
                    print(f"Error verifying temporary password: {e}")
                    # Continue to regular password check

        # Check if account is locked BEFORE attempting password verification
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            logger.warning(
                f"Login attempt blocked - Account locked for user: {email}. "
                f"Locked until: {user.locked_until}. "
                f"Failed attempts: {user.failed_login_attempts}"
            )
            raise HTTPException(
                status_code=http_status.HTTP_423_LOCKED,
                detail="account_locked",
            )

        # If we get here, check the regular password
        try:
            if not verify_password(password, user.hashed_password):
                logger.warning(
                    f"Password verification failed for user: {email}. "
                    f"Current failed attempts: {user.failed_login_attempts}"
                )
                try:
                    # Increment failed login attempts with progressive lockout
                    failed_attempts = user.failed_login_attempts + 1

                    # Progressive lockout strategy:
                    # 5 attempts: 5 minutes
                    # 10 attempts: 15 minutes
                    # 15 attempts: 30 minutes
                    # 20+ attempts: 60 minutes
                    lockout_duration = None
                    if failed_attempts >= 5:
                        if failed_attempts < 10:
                            lockout_duration = now + timedelta(minutes=5)
                        elif failed_attempts < 15:
                            lockout_duration = now + timedelta(minutes=15)
                        elif failed_attempts < 20:
                            lockout_duration = now + timedelta(minutes=30)
                        else:
                            lockout_duration = now + timedelta(minutes=60)

                    stmt = (
                        update(User)
                        .where(User.id == user.id)
                        .values(
                            failed_login_attempts=failed_attempts,
                            locked_until=lockout_duration,
                            updated_at=now,
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()

                    # Log account lockout
                    if lockout_duration:
                        logger.warning(
                            f"Account locked for user: {email}. "
                            f"Failed attempts: {failed_attempts}. "
                            f"Locked until: {lockout_duration}"
                        )
                except Exception as e:
                    logger.error(f"Error updating failed login attempts: {e}")
                    try:
                        await session.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Error during rollback: {rollback_error}")
                return None, False
        except Exception as e:
            print(f"Error verifying password: {e}")
            return None, False

        # Check if account is active
        print(f"Checking account status: {user.status}")
        if user.status != UserStatus.ACTIVE.value:
            print(f"Account is not active for user: {email}, status: {user.status}")
            return None, False

        # Check if email is verified
        print(f"Checking email verification status: {user.is_verified}")
        if not user.is_verified:
            print(f"Email not verified for user: {email}")
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="email_not_verified",
            )

        # Check for auto-enabling MFA based on grace period
        from app.services.email_mfa import email_mfa_service

        try:
            await email_mfa_service.check_and_auto_enable_mfa(user, session)
        except Exception as e:
            logger.error(
                f"Error during auto-enable MFA check for user {user.id}: {str(e)}"
            )

        # Check MFA if enabled (TOTP, SMS, or Email)
        has_totp_mfa = user.mfa_enabled and user.mfa_secret
        has_sms_mfa = user.sms_mfa_enabled and user.phone_verified
        has_email_mfa = user.email_mfa_enabled

        logger.info(
            f"MFA check for user {user.id}: TOTP={has_totp_mfa}, SMS={has_sms_mfa}, Email={has_email_mfa}"
        )

        # Check if device has valid MFA bypass (24-hour window)
        device_has_mfa_bypass = False
        if request and (has_totp_mfa or has_sms_mfa or has_email_mfa):
            from app.services.mfa_device_service import mfa_device_service

            device_has_mfa_bypass = await mfa_device_service.check_device_mfa_bypass(
                user, request, session
            )
            if device_has_mfa_bypass:
                logger.info(f"Device has valid MFA bypass for user {user.id}")

        if (
            (has_totp_mfa or has_sms_mfa or has_email_mfa)
            and not totp_code
            and not device_has_mfa_bypass
        ):
            # Determine which MFA methods are available and build appropriate message
            available_methods = []
            if has_totp_mfa:
                available_methods.append("TOTP")
            if has_sms_mfa:
                available_methods.append("SMS")
            if has_email_mfa:
                available_methods.append("Email")

            if len(available_methods) > 1:
                methods_str = " or ".join(available_methods)
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"MFA code required ({methods_str})",
                )
            elif has_totp_mfa:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="TOTP code required",
                )
            elif has_sms_mfa:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="SMS code required",
                )
            elif has_email_mfa:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Email code required",
                )

        # Verify MFA code if provided
        if totp_code:
            mfa_valid = False
            mfa_method_used = None

            # Try TOTP verification first
            if (
                has_totp_mfa
                and user.mfa_secret
                and verify_totp(totp_code, user.mfa_secret)
            ):
                mfa_valid = True
                mfa_method_used = "totp"

            # Try SMS verification if TOTP failed or not available
            if not mfa_valid and has_sms_mfa:
                # Import SMS MFA service to verify code
                from app.services.sms_mfa import sms_mfa_service

                try:
                    # Verify SMS MFA code
                    await sms_mfa_service.verify_mfa_code(user, totp_code, session)
                    mfa_valid = True
                    mfa_method_used = "sms"
                except HTTPException:
                    # SMS verification failed
                    pass

            # Try Email verification if TOTP and SMS failed or not available
            if not mfa_valid and has_email_mfa:
                try:
                    # Verify Email MFA code
                    await email_mfa_service.verify_mfa_code(user, totp_code, session)
                    mfa_valid = True
                    mfa_method_used = "email"
                except HTTPException:
                    # Email verification failed
                    pass

            if not mfa_valid:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Invalid MFA code",
                )

            # Record successful MFA verification for 24-hour bypass
            if mfa_valid and mfa_method_used and request:
                try:
                    from app.services.mfa_device_service import mfa_device_service

                    await mfa_device_service.record_mfa_verification(
                        user, request, session, mfa_method_used
                    )
                except Exception as e:
                    logger.error(
                        f"Error recording MFA verification for user {user.id}: {str(e)}"
                    )
                    # Don't fail the login if we can't record the bypass

        try:
            # Reset failed login attempts and update last login
            # Use the same timezone format for all datetime objects
            now = datetime.now(timezone.utc)
            stmt = (
                update(User)
                .where(User.id == user.id)
                .values(
                    failed_login_attempts=0,
                    locked_until=None,
                    last_login=now,
                    updated_at=now,  # Ensure updated_at is also timezone-aware
                )
            )
            await session.execute(stmt)
            await session.commit()
        except Exception as e:
            print(f"Error updating login information: {e}")
            try:
                await session.rollback()
            except Exception as rollback_error:
                print(f"Error during rollback: {rollback_error}")

        # Check if password is temporary and needs to be changed
        password_change_required = (
            getattr(user, "is_password_temporary", False) or temp_password_detected
        )

        return user, password_change_required
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in authenticate_user: {e}")
        return None, False


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user."""
    # Check if user with this email already exists
    normalized_email = normalize_email(user_data.email)
    existing_user = await get_user_by_email(session, normalized_email)
    if existing_user:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create verification token
    verification_token = uuid.uuid4()

    # Generate a secure password if not provided
    from app.core.password_utils import generate_secure_password

    password = user_data.password
    is_password_temporary = user_data.is_one_time_password

    if password is None:
        password = generate_secure_password()
        is_password_temporary = True

    # Create user
    new_user = User(
        email=normalized_email,
        hashed_password=get_password_hash(password),
        full_name=user_data.full_name,
        status=UserStatus.ACTIVE.value,  # Set to active by default
        is_verified=False,
        verification_token=verification_token,
        is_password_temporary=is_password_temporary,
        application_admin=user_data.application_admin,
    )
    session.add(new_user)
    await session.commit()

    # Refresh to get the full user object
    try:
        await session.refresh(new_user)
    except Exception as e:
        print(f"Error refreshing user: {e}")

        # Get the user from the database instead of refreshing
        stmt = select(User).where(User.email == user_data.email)
        result = await session.execute(stmt)
        found_user = result.scalars().first()
        if found_user is not None:
            new_user = found_user

    # Disabled verification step
    # from app.services.email_service import send_verification_email

    # # Extract name from full_name or use empty string
    # name = new_user.full_name.split()[0] if new_user.full_name else ""

    # Make sure to make this the last line before return if re-enabling
    # await send_verification_email(new_user.email, name, str(verification_token))

    # Send welcome email with temporary password instead of verification email
    from app.services.email_service import send_welcome_email_with_temp_password
    from datetime import datetime, timezone, timedelta

    # Extract name from full_name or use empty string
    name = new_user.full_name.split()[0] if new_user.full_name else ""

    # Set up temporary password fields and send welcome email
    # Update user with temporary password fields
    temp_password_hash = get_password_hash(password)
    temp_password_expiry = datetime.now(timezone.utc) + timedelta(hours=48)

    # Update the user with temporary password fields
    from sqlalchemy import update

    update_stmt = (
        update(User)
        .where(User.id == new_user.id)
        .values(
            temporary_hashed_password=temp_password_hash,
            temporary_password_expiry=temp_password_expiry,
            is_password_temporary=True,
        )
    )
    await session.execute(update_stmt)
    await session.commit()

    # Send welcome email with temporary password
    try:
        await send_welcome_email_with_temp_password(new_user.email, name, password)
        print(f"Welcome email with temporary password sent to {new_user.email}")
    except Exception as e:
        print(f"Error sending welcome email to {new_user.email}: {e}")

    return new_user


async def create_user_session(
    session: AsyncSession, user_id: int, request: Request
) -> Tuple[str, str]:
    """Create a new user session and return tokens."""
    # Get the current tenant ID from the request
    from db_core.middleware import get_current_tenant_id

    tenant_id = get_current_tenant_id()

    # Check if session is None
    if session is None:
        print(f"WARNING: Session is None in create_user_session for user ID {user_id}")
        # Create tokens directly without storing the session
        access_token = create_access_token(user_id, tenant_id=tenant_id)
        refresh_token = create_refresh_token(user_id, tenant_id=tenant_id)
        print(f"Created tokens directly for user ID {user_id} without storing session")
        return access_token, refresh_token

    try:
        # Get user to check if they have a temporary password flag
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if user:
            print(
                f"Creating session for user {user.email} (ID: {user.id}), is_password_temporary={user.is_password_temporary}"
            )

            if user.is_password_temporary:
                print(
                    f"User {user.email} has temporary password, invalidating all existing sessions before creating new one"
                )
                try:
                    stmt = (
                        update(Session)
                        .where(Session.user_id == user_id)
                        .values(is_active=False)
                    )
                    await session.execute(stmt)
                    await session.commit()
                    print(
                        f"Successfully invalidated existing sessions for user {user.email}"
                    )
                except Exception as invalidate_error:
                    print(f"Error invalidating existing sessions: {invalidate_error}")
                    try:
                        await session.rollback()
                    except Exception:
                        pass
    except Exception as e:
        print(f"Error getting user in create_user_session: {e}")
        # Continue without user info

    # Create tokens with tenant ID
    access_token = create_access_token(user_id, tenant_id=tenant_id)
    refresh_token = create_refresh_token(user_id, tenant_id=tenant_id)

    try:
        # Store session
        new_session = Session(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        session.add(new_session)
        await session.commit()
    except Exception as e:
        print(f"Error storing session in create_user_session: {e}")
        try:
            await session.rollback()
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}")
        # Continue with the tokens even if we couldn't store the session

    try:
        # Log activity
        await log_user_activity(
            session,
            user_id,
            "login",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as e:
        print(f"Error logging activity in create_user_session: {e}")
        # Continue even if we couldn't log the activity

    return access_token, refresh_token


async def verify_refresh_token(
    session: AsyncSession, refresh_token: str
) -> Optional[int]:
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
    stmt = (
        update(Session)
        .where(Session.refresh_token == refresh_token)
        .values(is_active=False)
    )
    await session.execute(stmt)
    await session.commit()
    # For SQLAlchemy 2.0, we need to check if any rows were affected
    return True  # Simplified for now, as rowcount might not be directly accessible


async def invalidate_all_sessions(session: AsyncSession, user_id: int) -> bool:
    """Invalidate all sessions for a user."""
    try:
        stmt = update(Session).where(Session.user_id == user_id).values(is_active=False)
        await session.execute(stmt)
        await session.commit()
        print(f"Successfully invalidated all sessions for user ID {user_id}")
        return True
    except Exception as e:
        print(f"Error invalidating all sessions for user ID {user_id}: {e}")
        try:
            await session.rollback()
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}")
        return False


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
    await log_user_activity(session, user_id, "mfa_activated")

    return True
