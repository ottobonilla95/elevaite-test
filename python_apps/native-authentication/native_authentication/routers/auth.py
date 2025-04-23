from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime

from native_authentication.auth import (
    get_user_by_username,
    get_current_user,
    blacklist_token,
)
from native_authentication.core.config import settings
from native_authentication.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from native_authentication.db.base import get_db
from native_authentication.models.token import Token, TokenPayload, RefreshToken
from native_authentication.models.user import User, UserCreate, UserOut


def get_auth_router(prefix: str = "/auth") -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["authentication"])

    @router.post("/register", response_model=UserOut)
    async def register(user_create: UserCreate, db: Session = Depends(get_db)):
        # Check if user already exists
        if get_user_by_username(db, user_create.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Create new user
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=get_password_hash(user_create.password),
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    @router.post("/login", response_model=Token)
    async def login(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
    ):
        # Authenticate user
        user = get_user_by_username(db, form_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @router.post("/refresh", response_model=Token)
    async def refresh_token(token_data: RefreshToken, db: Session = Depends(get_db)):
        try:
            # Decode refresh token
            payload = jwt.decode(
                token_data.refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            token_payload = TokenPayload(**payload)

            # Validate token
            if token_payload.type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check expiration
            if (
                token_payload.exp is None
                or datetime.fromtimestamp(token_payload.exp) < datetime.utcnow()
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get user
            user_id = int(token_payload.sub)
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create new access token
            access_token = create_access_token(subject=user.id)

            return {
                "access_token": access_token,
                "token_type": "bearer",
            }
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @router.post("/logout", status_code=status.HTTP_200_OK)
    async def logout(
        current_user: User = Depends(get_current_user),
        token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login")),
        db: Session = Depends(get_db),
    ):
        try:
            # Decode token to get expiration
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))

            # Blacklist the token
            blacklist_token(
                db=db,
                token=token,
                token_type="access",
                user_id=current_user.id,
                expires_at=expires_at,
            )

            return {"message": "Successfully logged out"}
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return router
