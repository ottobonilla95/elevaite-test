from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.db.models import User


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current user and verify they are a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
