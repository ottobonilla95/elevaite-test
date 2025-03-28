from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime

from native_authentication.core.config import settings
from native_authentication.db.base import get_db
from native_authentication.models.token import TokenPayload
from native_authentication.models.user import User
from native_authentication.models.token_blacklist import TokenBlacklist

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_user(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def is_token_blacklisted(db: Session, token: str) -> bool:
    return (
        db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        is not None
    )


def blacklist_token(
    db: Session, token: str, token_type: str, user_id: int, expires_at: datetime
) -> None:
    token_blacklist = TokenBlacklist(
        token=token, token_type=token_type, user_id=user_id, expires_at=expires_at
    )
    db.add(token_blacklist)
    db.commit()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if is_token_blacklisted(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if token_data.type != "access":
            raise credentials_exception

        if (
            token_data.exp is None
            or datetime.fromtimestamp(token_data.exp) < datetime.utcnow()
        ):
            raise credentials_exception

        user_id = token_data.sub
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(db, int(user_id))
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
