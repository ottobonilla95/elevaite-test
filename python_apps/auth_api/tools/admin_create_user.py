#!/usr/bin/env python3
"""
Script to create or update users in the auth database without admin checks.

This script allows creating new users or resetting passwords for existing users
across all tenants in the auth database. It bypasses the normal admin checks
that would be required through the API.

Usage:
    python admin_create_user.py

The script will prompt for:
1. Email address
2. Password (or auto-generate one)
3. Full name
4. Whether the user should be an admin
5. Whether the password should be one-time (requiring reset on first login)
6. Which tenant(s) to create the user in

If the user already exists, it will prompt to reset their password.
"""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
import getpass
import re

# Add the parent directory to sys.path to allow importing from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select, update
from db_core.utils import (
    get_schema_name,
)

from app.db.models import User, UserStatus
from app.core.security import get_password_hash
from app.core.password_utils import normalize_email
from app.core.password_utils import generate_secure_password
from app.core.multitenancy import DEFAULT_TENANTS, multitenancy_settings


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    """Get user by email in the current tenant context."""
    normalized_email = normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized_email))
    return result.scalars().first()


async def create_user_in_tenant(
    engine: AsyncSession,
    tenant_id: str,
    email: str,
    password: str,
    full_name: str,
    is_superuser: bool,
    is_one_time_password: bool,
) -> None:
    """Create a user in a specific tenant schema."""
    email = normalize_email(email)

    # Create session factory
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create session
    async with async_session() as session:
        try:
            # Set search path to tenant schema
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            await session.execute(text(f'SET search_path TO "{schema_name}", public'))

            # Check if user already exists
            existing_user = await get_user_by_email(session, email)

            if existing_user:
                print(f"User {email} already exists in tenant {tenant_id}")
                return existing_user

            # Create user
            now = datetime.now(timezone.utc)
            verification_token = uuid.uuid4()
            hashed_password = get_password_hash(password)

            # Create new user
            new_user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                status=UserStatus.ACTIVE.value,
                is_verified=True,  # Set to verified by default
                is_superuser=is_superuser,
                is_password_temporary=is_one_time_password,
                verification_token=verification_token,
                created_at=now,
                updated_at=now,
                failed_login_attempts=0,
                mfa_enabled=False,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            print(f"Created user {email} with ID {new_user.id} in tenant {tenant_id}")
            return new_user

        except Exception as e:
            await session.rollback()
            print(f"Error creating user in tenant {tenant_id}: {e}")
            raise


async def reset_user_password(
    engine: AsyncSession,
    tenant_id: str,
    email: str,
    new_password: str,
    is_one_time_password: bool,
) -> None:
    """Reset password for an existing user."""
    # Create session factory
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create session
    async with async_session() as session:
        try:
            # Set search path to tenant schema
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            await session.execute(text(f'SET search_path TO "{schema_name}", public'))

            # Find user by email
            existing_user = await get_user_by_email(session, email)

            if not existing_user:
                print(f"User {email} not found in tenant {tenant_id}")
                return None

            # Update password
            hashed_password = get_password_hash(new_password)
            now = datetime.now(timezone.utc)

            stmt = (
                update(User)
                .where(User.id == existing_user.id)
                .values(
                    hashed_password=hashed_password,
                    is_password_temporary=is_one_time_password,
                    updated_at=now,
                    password_reset_token=None,
                    password_reset_expires=None,
                )
            )

            await session.execute(stmt)
            await session.commit()

            print(f"Reset password for user {email} in tenant {tenant_id}")
            return existing_user

        except Exception as e:
            await session.rollback()
            print(f"Error resetting password in tenant {tenant_id}: {e}")
            raise


def validate_email(email: str) -> bool:
    """Validate email format."""
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_regex, email))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 9:
        return False, "Password must be at least 9 characters long"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, ""


async def main():
    """Create or update a user in all tenant schemas."""
    # Database connection parameters
    db_host = input("Database host [localhost]: ") or "localhost"
    db_port = input("Database port [5433]: ") or "5433"
    db_user = input("Database user [elevaite]: ") or "elevaite"
    db_password = getpass.getpass("Database password [elevaite]: ") or "elevaite"
    db_name = input("Database name [elevaite]: ") or "elevaite"

    # Create database URL
    db_url = (
        f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    # Create engine
    engine = create_async_engine(db_url)

    # Get user details
    while True:
        email = input("User email: ")
        if validate_email(email):
            break
        print("Invalid email format. Please try again.")

    email = normalize_email(email)

    # Check if user exists in any tenant
    user_exists = False
    for tenant_id in DEFAULT_TENANTS:
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            await session.execute(text(f'SET search_path TO "{schema_name}", public'))
            existing_user = await get_user_by_email(session, email)
            if existing_user:
                user_exists = True
                print(f"User {email} exists in tenant {tenant_id}")

    if user_exists:
        reset_password = (
            input("User already exists. Reset password? (y/n): ").lower() == "y"
        )
        if not reset_password:
            print("Operation cancelled.")
            await engine.dispose()
            return

        # Get new password
        use_generated = input("Generate secure password? (y/n): ").lower() == "y"
        if use_generated:
            new_password = generate_secure_password()
            print(f"Generated password: {new_password}")
        else:
            while True:
                new_password = getpass.getpass("New password: ")
                is_valid, error_msg = validate_password(new_password)
                if is_valid:
                    break
                print(f"Invalid password: {error_msg}")
                print(
                    "Password must be at least 9 characters with uppercase, lowercase, number, and special character"
                )

        is_one_time = (
            input(
                "Make password one-time (require change on first login)? (y/n): "
            ).lower()
            == "y"
        )

        # Select tenants
        selected_tenants = []
        print("\nAvailable tenants:")
        for i, tenant in enumerate(DEFAULT_TENANTS, 1):
            print(f"{i}. {tenant}")

        tenant_input = input("Enter tenant numbers (comma-separated) or 'all': ")
        if tenant_input.lower() == "all":
            selected_tenants = DEFAULT_TENANTS
        else:
            try:
                tenant_indices = [
                    int(idx.strip()) - 1 for idx in tenant_input.split(",")
                ]
                selected_tenants = [
                    DEFAULT_TENANTS[idx]
                    for idx in tenant_indices
                    if 0 <= idx < len(DEFAULT_TENANTS)
                ]
            except (ValueError, IndexError):
                print("Invalid tenant selection. Using all tenants.")
                selected_tenants = DEFAULT_TENANTS

        # Reset password in selected tenants
        for tenant_id in selected_tenants:
            try:
                await reset_user_password(
                    engine, tenant_id, email, new_password, is_one_time
                )
            except Exception as e:
                print(f"Error resetting password in tenant {tenant_id}: {e}")

    else:
        # Get user details for new user
        full_name = input("Full name: ")

        use_generated = input("Generate secure password? (y/n): ").lower() == "y"
        if use_generated:
            password = generate_secure_password()
            print(f"Generated password: {password}")
        else:
            while True:
                password = getpass.getpass("Password: ")
                is_valid, error_msg = validate_password(password)
                if is_valid:
                    break
                print(f"Invalid password: {error_msg}")
                print(
                    "Password must be at least 9 characters with uppercase, lowercase, number, and special character"
                )

        is_superuser = input("Make user an admin? (y/n): ").lower() == "y"
        is_one_time = (
            input(
                "Make password one-time (require change on first login)? (y/n): "
            ).lower()
            == "y"
        )

        # Select tenants
        selected_tenants = []
        print("\nAvailable tenants:")
        for i, tenant in enumerate(DEFAULT_TENANTS, 1):
            print(f"{i}. {tenant}")

        tenant_input = input("Enter tenant numbers (comma-separated) or 'all': ")
        if tenant_input.lower() == "all":
            selected_tenants = DEFAULT_TENANTS
        else:
            try:
                tenant_indices = [
                    int(idx.strip()) - 1 for idx in tenant_input.split(",")
                ]
                selected_tenants = [
                    DEFAULT_TENANTS[idx]
                    for idx in tenant_indices
                    if 0 <= idx < len(DEFAULT_TENANTS)
                ]
            except (ValueError, IndexError):
                print("Invalid tenant selection. Using all tenants.")
                selected_tenants = DEFAULT_TENANTS

        # Create user in selected tenants
        for tenant_id in selected_tenants:
            try:
                await create_user_in_tenant(
                    engine,
                    tenant_id,
                    email,
                    password,
                    full_name,
                    is_superuser,
                    is_one_time,
                )
            except Exception as e:
                print(f"Error creating user in tenant {tenant_id}: {e}")

    # Close engine
    await engine.dispose()

    print("\nOperation completed.")


if __name__ == "__main__":
    asyncio.run(main())
