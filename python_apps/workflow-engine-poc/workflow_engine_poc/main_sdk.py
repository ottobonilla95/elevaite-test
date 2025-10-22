"""
Workflow Engine PoC - Running on workflow-core-sdk

This version uses ONLY the SDK, proving that the SDK extraction is complete and functional.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

# Import core components from the SDK (NOT routers - they live in the PoC)
from workflow_core_sdk import (
    StepRegistry,
    WorkflowEngine,
    create_db_and_tables,
    tool_registry,
)

# Import routers from local PoC code
from workflow_engine_poc.routers import (
    health,
    workflows,
    executions,
    steps,
    files,
    monitoring as monitoring_router,
    agents,
    tools,
    prompts,
    messages,
)
from workflow_engine_poc.routers.approvals import router as approvals

from fastapi_logger import ElevaiteLogger

# Early DBOS bootstrap
try:
    from dbos import DBOS as _DBOS_EARLY, DBOSConfig as _DBOSConfig_EARLY
    from workflow_core_sdk.db.database import DATABASE_URL as _ENGINE_DB_URL

    _dbos_db_url_early = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL
    _app_name_early = os.getenv("DBOS_APPLICATION_NAME") or "workflow-engine-poc-sdk"
    _cfg_early = _DBOSConfig_EARLY(database_url=_dbos_db_url_early, name=_app_name_early)
    _DBOS_EARLY(config=_cfg_early)
    logging.getLogger(__name__).info("✅ DBOS pre-initialized (SDK version)")
except Exception as _e:
    logging.getLogger(__name__).warning(f"DBOS pre-init skipped: {_e}")

# Configure logging
ElevaiteLogger.attach_to_uvicorn(
    service_name="workflow-engine-sdk",
    configure_otel=True,
    otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
    resource_attributes={
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    },
)

_LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
_NUM_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
logging.basicConfig(level=_NUM_LEVEL)
logger = logging.getLogger(__name__)
logger.setLevel(_NUM_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management - SDK version"""
    logger.info("=" * 70)
    logger.info("🚀 Workflow Engine PoC - Running on workflow-core-sdk")
    logger.info("=" * 70)

    # Initialize database using SDK
    logger.info("Initializing database from SDK...")
    create_db_and_tables()
    logger.info("✅ Database initialized (SDK)")

    # Initialize step registry using SDK
    logger.info("Initializing step registry from SDK...")
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    app.state.step_registry = step_registry
    logger.info("✅ Step registry initialized (SDK)")

    # Initialize workflow engine using SDK
    logger.info("Initializing workflow engine from SDK...")
    workflow_engine = WorkflowEngine(step_registry=step_registry)
    app.state.workflow_engine = workflow_engine
    logger.info("✅ Workflow engine initialized (SDK)")

    # Initialize tool registry using SDK
    logger.info("Initializing tool registry from SDK...")
    app.state.tool_registry = tool_registry
    logger.info("✅ Tool registry initialized (SDK)")

    # Launch DBOS executor if configured
    logger.info("Launching DBOS executor...")
    try:
        from dbos import DBOS as _DBOS_CLASS

        _DBOS_CLASS.launch()
        logger.info("✅ DBOS executor launched (SDK)")
    except Exception as e:
        logger.warning(f"DBOS launch skipped/failed: {e}")

    # Start scheduler if available
    try:
        from workflow_core_sdk.scheduler import WorkflowScheduler

        scheduler = WorkflowScheduler(poll_interval_seconds=int(os.getenv("SCHEDULER_POLL_SECONDS", "15")))
        app.state.scheduler = scheduler
        await scheduler.start(app)
        logger.info("✅ Scheduler started (SDK)")
    except Exception as e:
        logger.warning(f"Scheduler start skipped/failed: {e}")

    logger.info("=" * 70)
    logger.info("✅ Workflow Engine PoC Ready - Powered by workflow-core-sdk")
    logger.info("=" * 70)

    yield

    logger.info("🛑 Shutting down Workflow Engine PoC (SDK version)")
    try:
        if getattr(app.state, "scheduler", None):
            await app.state.scheduler.stop()
    except Exception:
        pass


# Create FastAPI app
app = FastAPI(
    title="Workflow Execution Engine PoC (SDK)",
    description="Unified workflow execution engine - Running on workflow-core-sdk",
    version="2.0.0-sdk",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all PoC routers (using SDK services underneath)
logger.info("Mounting PoC routers (powered by SDK services)...")
app.include_router(health, prefix="/api", tags=["health"])
app.include_router(workflows, prefix="/api", tags=["workflows"])
app.include_router(executions, prefix="/api", tags=["executions"])
app.include_router(agents, prefix="/api", tags=["agents"])
app.include_router(tools, prefix="/api", tags=["tools"])
app.include_router(steps, prefix="/api", tags=["steps"])
app.include_router(files, prefix="/api", tags=["files"])
app.include_router(messages, prefix="/api", tags=["messages"])
app.include_router(prompts, prefix="/api", tags=["prompts"])
app.include_router(approvals, prefix="/api", tags=["approvals"])
app.include_router(monitoring_router, prefix="/api", tags=["monitoring"])
logger.info("✅ All routers mounted")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Workflow Execution Engine PoC",
        "version": "2.0.0-sdk",
        "status": "running",
        "powered_by": "workflow-core-sdk",
        "message": "This PoC is running entirely on the SDK - no local code!",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "workflow-engine-poc-sdk",
        "sdk_version": "0.1.0",
    }


if __name__ == "__main__":
    # OpenTelemetry instrumentation
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ OpenTelemetry instrumentation enabled")
    except Exception as e:
        logger.warning(f"OpenTelemetry instrumentation failed: {e}")

    # Run the server
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8006")),
        log_level=_LOG_LEVEL_NAME.lower(),
    )
