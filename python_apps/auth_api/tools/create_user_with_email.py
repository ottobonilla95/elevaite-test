#!/usr/bin/env python3
"""
Script to create a user and send a welcome email.

This script creates a new user in the auth database and sends a welcome email
using the SendGrid API integration.

Usage:
    python create_user_with_email.py
"""

import asyncio
import sys
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
import getpass
import re

# Add the parent directory to sys.path to allow importing from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select

from app.core.security import get_password_hash
from app.db.models import User, UserStatus
from app.core.multitenancy import DEFAULT_TENANTS, multitenancy_settings
from db_core.utils import get_schema_name
from app.core.password_utils import generate_secure_password
from app.services.email_service import send_welcome_email_with_temp_password
from app.core.config import settings


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    """Get user by email in the current tenant context."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user_in_tenant(
    engine: AsyncSession,
    tenant_id: str,
    email: str,
    password: str,
    full_name: str,
    is_superuser: bool,
    is_one_time_password: bool,
) -> User:
    """Create a user in a specific tenant schema."""
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


def validate_email(email: str) -> bool:
    """Validate email format."""
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_regex, email))


async def main():
    """Create a user and send a welcome email."""
    print("Create User and Send Welcome Email")
    print("==================================")
    
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

    full_name = input("Full name: ")
    
    # Generate a secure password
    password = generate_secure_password()
    print(f"Generated password: {password}")
    
    is_superuser = input("Make user an admin? (y/n): ").lower() == "y"
    is_one_time = True  # Always make it one-time password when sending email
    
    # Select tenant
    print("\nAvailable tenants:")
    for i, tenant in enumerate(DEFAULT_TENANTS, 1):
        print(f"{i}. {tenant}")
    
    tenant_idx = int(input("Select tenant (number): ")) - 1
    if 0 <= tenant_idx < len(DEFAULT_TENANTS):
        tenant_id = DEFAULT_TENANTS[tenant_idx]
    else:
        print("Invalid tenant selection. Using first tenant.")
        tenant_id = DEFAULT_TENANTS[0]
    
    # Create user
    try:
        user = await create_user_in_tenant(
            engine, 
            tenant_id, 
            email, 
            password, 
            full_name, 
            is_superuser, 
            is_one_time
        )
        
        if user:
            # Send welcome email
            print(f"Sending welcome email to {email}...")
            # Extract first name from full name
            first_name = full_name.split()[0] if full_name else "User"
            result = await send_welcome_email_with_temp_password(email, first_name, password)
            if result:
                print(f"Welcome email sent successfully to {email}")
            else:
                print(f"Failed to send welcome email to {email}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Close engine
    await engine.dispose()
    
    print("\nOperation completed.")


if __name__ == "__main__":
    asyncio.run(main())
