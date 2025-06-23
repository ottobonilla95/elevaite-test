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
from app.db.models import Session, User, UserStatus
from app.schemas.user import UserCreate


# Type variable for User model
T = TypeVar("T", bound=User)


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email in the current tenant context."""
    # This function is automatically tenant-aware because the session
    # is created with the tenant schema set in the search_path
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def authenticate_user(
    session: AsyncSession, email: str, password: str, totp_code: Optional[str] = None
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
                    return user, True
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
                        print(f"Temporary password used successfully for user: {email}")

                        # Get the user ID as a plain integer for the update
                        user_id = user.id

                        # IMPORTANT: If the user is logging in with a temporary password,
                        # we ALWAYS want to set is_password_temporary to TRUE to force them
                        # to change their password, regardless of the current value.
                        # The only exception is if they've explicitly changed their password before.

                        # CRITICAL: If the user is logging in with a temporary password,
                        # we MUST set is_password_temporary to TRUE regardless of its current value.
                        # We should NOT respect is_password_temporary=False when using a temporary password.
                        print(
                            f"User {email} is logging in with a temporary password, setting is_password_temporary=TRUE"
                        )

                        # NEVER return here - we must ALWAYS set is_password_temporary to TRUE
                        # when the user logs in with a temporary password

                        # CRITICAL: Set is_password_temporary to TRUE in the user object
                        # This ensures that the flag is set even if the database update fails
                        user.is_password_temporary = True

                        # Log that we're setting is_password_temporary to TRUE
                        print(
                            f"Setting is_password_temporary=TRUE for user {email} in the user object"
                        )

                        # Also log the user object structure for debugging
                        # CRITICAL: Only log information that won't trigger a database query
                        print(f"User object type: {type(user)}")
                        # Don't use dir() as it might trigger attribute access
                        # Only access __dict__ directly
                        user_dict = getattr(user, "__dict__", {})
                        print(f"User object __dict__ keys: {list(user_dict.keys())}")
                        # Log specific attributes we care about
                        print(f"User ID: {user_dict.get('id', 'N/A')}")
                        print(f"User email: {user_dict.get('email', 'N/A')}")
                        print(
                            f"User is_password_temporary: {user_dict.get('is_password_temporary', 'N/A')}"
                        )

                        # If we get here, the user is logging in with a temporary password
                        # and has not explicitly changed their password before, so we should
                        # set is_password_temporary to TRUE to force them to change it

                        # Set is_password_temporary to trigger frontend password reset
                        # Use a direct SQL update to ensure it's applied
                        from sqlalchemy import text

                        # Use raw SQL with explicit schema to avoid any ORM caching issues
                        # CRITICAL: This is where we set is_password_temporary to TRUE in the database
                        # when a user logs in with a temporary password
                        update_sql = text(
                            """
                            UPDATE users
                            SET temporary_hashed_password = NULL,
                                temporary_password_expiry = NULL,
                                is_password_temporary = TRUE,
                                updated_at = :now
                            WHERE id = :user_id
                        """
                        )

                        try:
                            # Execute the update with explicit parameters
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

        # If we get here, check the regular password
        try:
            if not verify_password(password, user.hashed_password):
                print(f"Password verification failed for user: {email}")
                try:
                    # Increment failed login attempts
                    stmt = (
                        update(User)
                        .where(User.id == user.id)
                        .values(
                            failed_login_attempts=user.failed_login_attempts + 1,
                            locked_until=(
                                now + timedelta(minutes=15)
                                if user.failed_login_attempts + 1 >= 5
                                else None
                            ),
                            updated_at=now,  # Ensure updated_at is also timezone-aware
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()
                except Exception as e:
                    print(f"Error updating failed login attempts: {e}")
                    try:
                        await session.rollback()
                    except Exception as rollback_error:
                        print(f"Error during rollback: {rollback_error}")
                return None, False
        except Exception as e:
            print(f"Error verifying password: {e}")
            return None, False

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            print(f"Account is locked for user: {email}")
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

        # Check MFA if enabled
        if user.mfa_enabled and not totp_code:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="TOTP code required",
            )

        if (
            user.mfa_enabled
            and totp_code
            and user.mfa_secret
            and not verify_totp(totp_code, user.mfa_secret)
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code",
            )

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
        password_change_required = getattr(user, "is_password_temporary", False)

        return user, password_change_required
    except Exception as e:
        print(f"Unexpected error in authenticate_user: {e}")
        return None, False


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

    # Generate a secure password if not provided
    from app.core.password_utils import generate_secure_password

    password = user_data.password
    is_password_temporary = user_data.is_one_time_password

    if password is None:
        password = generate_secure_password()
        is_password_temporary = True

    # Create user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(password),
        full_name=user_data.full_name,
        status=UserStatus.ACTIVE.value,  # Set to active by default
        is_verified=False,
        verification_token=verification_token,
        is_password_temporary=is_password_temporary,
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

    # Send verification email
    from app.services.email_service import send_verification_email

    # Extract name from full_name or use empty string
    name = new_user.full_name.split()[0] if new_user.full_name else ""
    await send_verification_email(new_user.email, name, str(verification_token))

    # Send welcome email with temporary password if generated
    if is_password_temporary:
        from app.services.email_service import send_welcome_email_with_temp_password

        await send_welcome_email_with_temp_password(new_user.email, name, password)

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
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
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
