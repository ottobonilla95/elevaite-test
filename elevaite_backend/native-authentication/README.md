# Native Authentication Module

A secure native authentication module for the elevAIte backend services.

## Features

- User registration and authentication
- JWT-based access and refresh tokens
- Token revocation and blacklisting
- Secure password hashing with bcrypt
- Easy integration with FastAPI applications

## Quick Start

```python
from fastapi import FastAPI, Depends
from native_authentication import get_auth_router, get_current_user, User

app = FastAPI()

# Add authentication routes
app.include_router(
    get_auth_router(),
    prefix="/auth",
    tags=["authentication"]
)

# Protected route example
@app.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    return {"message": f"Hello, {user.username}!"}
```

## Configuration

Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
DATABASE_URL=sqlite:///./auth.db
```

## Security Considerations

- Passwords are hashed using bcrypt
- JWTs are signed with a secret key
- Refresh tokens can be revoked
- Rate limiting is implemented for authentication endpoints
