"""Main FastAPI application."""

# Apply patches for third-party libraries
# These patches are applied automatically when imported
# pylint: disable=unused-import
from db_core.middleware import add_tenant_middleware
from app.patches import starlette_patch, passlib_patch  # noqa: F401
# pylint: enable=unused-import

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer

from db_core import TenantMiddleware

from app.core.config import settings
from app.core.multitenancy import multitenancy_settings
from app.db.tenant_db import initialize_db
from app.routers import auth

security = HTTPBearer()


@asynccontextmanager
async def lifespan(_app: FastAPI):  # pylint: disable=unused-argument
    """Initialize database on startup."""
    # Initialize tenant schemas and tables
    await initialize_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description="Secure Authentication API",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add tenant middleware
# app.add_middleware(TenantMiddleware, settings=multitenancy_settings)
add_tenant_middleware(app, settings=multitenancy_settings)

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Add CORS middleware with secure defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/api/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
