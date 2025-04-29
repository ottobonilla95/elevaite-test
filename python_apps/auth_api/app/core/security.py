"""Security utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

# Use passlib without the deprecated crypt module
from passlib.context import CryptContext

from app.core.config import settings
from app.db.orm import get_async_session

# Token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

# Password hashing with Argon2id (more secure than bcrypt)
password_hasher = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # 64MB memory usage
    parallelism=4,  # Number of parallel threads
    hash_len=32,  # Length of the hash in bytes
    salt_len=16,  # Length of the random salt in bytes
)

# Fallback for legacy password hashing (if needed)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto", argon2__rounds=3)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        # Use Argon2 for verification
        password_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        # Fallback to passlib for older hashes
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash using Argon2id."""
    return password_hasher.hash(password)


def create_access_token(
    subject: Union[str, Any], tenant_id: Optional[str] = None, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}

    # Add tenant_id to the token if provided
    if tenant_id:
        to_encode["tenant_id"] = tenant_id

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], tenant_id: Optional[str] = None) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}

    # Add tenant_id to the token if provided
    if tenant_id:
        to_encode["tenant_id"] = tenant_id

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str) -> Dict[str, Any]:
    """Verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)):
    """Get the current user from the token."""
    from db_core.middleware import get_current_tenant_id
    from app.db.models import User
    from sqlalchemy import select

    # Verify the token
    payload = verify_token(token, "access")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if the token's tenant matches the current tenant
    token_tenant_id = payload.get("tenant_id")
    current_tenant_id = get_current_tenant_id()

    if token_tenant_id != current_tenant_id:
        print(f"Token tenant mismatch: token={token_tenant_id}, current={current_tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not valid for this tenant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user from the database
    result = await session.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def generate_totp_secret() -> str:
    """Generate a secret key for TOTP-based 2FA."""
    return pyotp.random_base32()


def generate_totp_uri(secret: str, user_email: str) -> str:
    """Generate a TOTP URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name=settings.MFA_ISSUER)


def verify_totp(totp_code: str, totp_secret: str) -> bool:
    """Verify a TOTP code."""
    totp = pyotp.TOTP(totp_secret)
    return totp.verify(totp_code)
