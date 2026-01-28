"""
Code Execution Service - FastAPI Application

A secure code execution sandbox service using Nsjail for isolation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.config import settings
from .routers import execute, health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.service_name}...")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Default timeout: {settings.default_timeout_seconds}s")
    logger.info(f"Max memory: {settings.max_memory_mb}MB")

    # Check Nsjail availability
    from .services.sandbox import SandboxExecutor

    sandbox = SandboxExecutor()
    if sandbox.is_available():
        logger.info(f"✅ Nsjail available at {settings.nsjail_path}")
    else:
        logger.warning(f"⚠️ Nsjail not found at {settings.nsjail_path} - running in development mode (UNSAFE)")

    yield

    # Cleanup
    logger.info(f"Shutting down {settings.service_name}...")


# Create FastAPI app
app = FastAPI(
    title="Code Execution Service",
    description="Secure code execution sandbox service using Nsjail for isolation",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router)
app.include_router(execute.router)


# Add a simple root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.service_name,
        "version": "0.1.0",
        "docs": "/docs",
    }
