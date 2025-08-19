"""
Unified Workflow Execution Engine - FastAPI PoC

A clean, agnostic workflow execution engine that supports:
- Conditional, sequential, and parallel execution
- RPC-like step registration
- Simplified agent execution
- Database-backed configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from workflow_engine_poc.step_registry import StepRegistry
from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.database import get_database
from workflow_engine_poc.monitoring import monitoring

# Import all routers
from workflow_engine_poc.routers import (
    health,
    workflows,
    executions,
    steps,
    files,
    monitoring as monitoring_router,
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Workflow Execution Engine PoC")

    # Initialize database
    database = await get_database()
    logger.info("✅ Database initialized")
    app.state.database = database

    # Initialize step registry with built-in steps
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    logger.info("✅ Built-in steps registered")

    # Store registry in app state
    app.state.step_registry = step_registry
    app.state.workflow_engine = WorkflowEngine(step_registry)

    yield

    logger.info("🛑 Shutting down Workflow Execution Engine")


# Create FastAPI app
app = FastAPI(
    title="Unified Workflow Execution Engine",
    description="A clean, agnostic workflow execution engine PoC",
    version="1.0.0-poc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(executions.router)
app.include_router(steps.router)
app.include_router(files.router)
app.include_router(monitoring_router.router)


# All endpoints are now defined in routers


if __name__ == "__main__":
    uvicorn.run(
        "workflow_engine_poc.main:app",
        host="0.0.0.0",
        port=8006,  # Different port from agent-studio
        reload=True,
        log_level="info",
        reload_excludes=[
            "*.db",
            "*.sqlite",
            "*.sqlite3",
            "*.log",
            "*.tmp",
            "*.cache",
            "__pycache__/*",
            ".pytest_cache/*",
            "logs/*",
            "data/*",
            "*.json",  # Exclude JSON files that might be used for data storage
        ],
    )
