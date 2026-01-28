from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from db_core.middleware import add_tenant_middleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from fastapi_logger import ElevaiteLogger

from app.routers import auth
from app.routers import user
from app.routers import biometric
from app.core.config import settings
from app.db.tenant_db import initialize_db
from app.core.logging import attach_logger_to_app, logger
from app.core.multitenancy import multitenancy_settings

# Configure the logger for FastAPI and Uvicorn
attach_logger_to_app()

security = HTTPBearer()


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if (
            request.url.path.startswith("/api/auth")
            or request.url.path.startswith("/api/user")
            or request.url.path.startswith("/api/email-mfa")
            or request.url.path.startswith("/api/sms-mfa")
            or request.url.path.startswith("/api/admin")
        ):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):  # pylint: disable=unused-argument
    logger.info("Starting Auth API application")
    try:
        # Initialize tenant schemas and tables
        logger.info("Initializing database and tenant schemas")
        logger.info(f"Using database URL: {settings.DATABASE_URI[:50]}...")
        await initialize_db()
        logger.info("Database initialization completed successfully")

        ElevaiteLogger.force_reattach_to_uvicorn()

        # Start background tasks for cleaning up expired data
        import asyncio
        from app.tasks.cleanup_tasks import start_cleanup_tasks

        cleanup_task = asyncio.create_task(start_cleanup_tasks())
        logger.info("Started cleanup tasks (sessions and MFA verifications)")

        yield

        # Cancel cleanup task on shutdown
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("Cleanup tasks cancelled")
    finally:
        logger.info("Shutting down Auth API application")


app = FastAPI(
    title="Minimal Auth API",
    description="Minimal test version",
    version="0.1.0",
    lifespan=lifespan,
)
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     """Handle validation errors and log them properly"""
#     logger.error(f"❌ Validation error on {request.method} {request.url.path}")
#     logger.error(f"❌ Errors: {exc.errors()}")
#     logger.error(f"❌ Body: {exc.body}")

#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={
#             "detail": jsonable_encoder(exc.errors()),
#             "body": str(exc.body) if exc.body else None
#         },
#     )
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

app.add_middleware(NoCacheMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(biometric.router, prefix="/api")
# Include SMS MFA router
from app.routers import sms_mfa

app.include_router(sms_mfa.router, prefix="/api/sms-mfa", tags=["sms-mfa"])

# Include Email MFA router
from app.routers import email_mfa

app.include_router(email_mfa.router, prefix="/api/email-mfa", tags=["email-mfa"])

# Include Authorization (authz) router
from app.routers import authz

app.include_router(authz.router, prefix="/api/authz", tags=["authz"])

# Include RBAC management router
from app.routers import rbac

app.include_router(rbac.router, prefix="/api/rbac", tags=["rbac"])

# Include Policy management router
from app.routers import policies

app.include_router(policies.router, prefix="/api", tags=["policies"])

# Include Admin router
from app.routers import admin

app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


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


@app.get("/")
def root():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8004,
        reload=settings.DEBUG,
        reload_excludes=["*.git*", "*.pyc", "__pycache__", "*.log"]
        if settings.DEBUG
        else None,
    )
