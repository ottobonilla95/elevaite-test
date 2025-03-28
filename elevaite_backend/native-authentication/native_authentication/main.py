from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from native_authentication.core.config import settings
from native_authentication.routers import get_auth_router
from native_authentication.db.base import Base, engine
from native_authentication.auth import get_current_active_user

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="elevAIte Native Authentication API",
    description="API for authentication and user management",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(get_auth_router())


@app.get("/")
async def root(current_user=Depends(get_current_active_user)):
    return {
        "message": "Welcome to the elevAIte Native Authentication API",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "native_authentication.main:app", host="0.0.0.0", port=8000, reload=True
    )
