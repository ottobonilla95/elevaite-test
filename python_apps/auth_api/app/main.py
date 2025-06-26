from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer

from db_core.middleware import add_tenant_middleware

from app.core.config import settings
from app.core.logging import attach_logger_to_app, logger
from app.core.multitenancy import multitenancy_settings
from app.db.tenant_db import initialize_db
from app.routers import auth

# Configure the logger for FastAPI and Uvicorn
attach_logger_to_app()

security = HTTPBearer()


@asynccontextmanager
async def lifespan(_app: FastAPI):  # pylint: disable=unused-argument
    logger.info("Starting Auth API application")
    try:
        # Initialize tenant schemas and tables
        logger.info("Initializing database and tenant schemas")
        await initialize_db()
        logger.info("Database initialization completed successfully")

        # Force re-attachment to handle uvicorn command-line override
        from fastapi_logger import ElevaiteLogger

        ElevaiteLogger.force_reattach_to_uvicorn()

        yield
    finally:
        logger.info("Shutting down Auth API application")


app = FastAPI(
    title="Minimal Auth API",
    description="Minimal test version",
    version="0.1.0",
    lifespan=lifespan,
)

# Add tenant middleware with excluded paths for health and docs endpoints
excluded_paths = {
    r"^/api/health$": {"default_tenant": "default"},
    r"^/docs.*": {"default_tenant": "default"},
    r"^/redoc.*": {"default_tenant": "default"},
    r"^/openapi\.json$": {"default_tenant": "default"},
}
add_tenant_middleware(
    app, settings=multitenancy_settings, excluded_paths=excluded_paths
)

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/api/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called")
    return {"status": "healthy"}


@app.get("/api/test-logs", tags=["testing"])
def test_logs():
    """Test endpoint to demonstrate different log levels."""
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    return {"message": "Check the logs to see different colored log levels!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8004, reload=settings.DEBUG)
