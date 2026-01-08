"""
Unified Workflow Execution Engine - FastAPI PoC

A clean, agnostic workflow execution engine that supports:
- Conditional, sequential, and parallel execution
- RPC-like step registration
- Simplified agent execution
- Database-backed configuration
- Schema-based multitenancy for data isolation
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from workflow_engine_poc.step_registry import StepRegistry
from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.db.database import get_database, create_db_and_tables
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from fastapi_logger import ElevaiteLogger

# Multitenancy support
from db_core.middleware import add_tenant_middleware
from workflow_core_sdk.multitenancy import multitenancy_settings, DEFAULT_TENANTS
from workflow_core_sdk.db.tenant_db import initialize_tenant_db

# Early DBOS bootstrap to ensure decorators are bound before importing routers
# Skip DBOS in test mode to avoid SQLite compatibility issues
if not os.getenv("TESTING"):
    try:  # optional dependency; skip silently if not installed
        from dbos import DBOS as _DBOS_EARLY, DBOSConfig as _DBOSConfig_EARLY
        from workflow_engine_poc.db.database import DATABASE_URL as _ENGINE_DB_URL

        _dbos_db_url_early = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL
        _app_name_early = os.getenv("DBOS_APPLICATION_NAME") or "workflow-engine-poc"
        _cfg_early = _DBOSConfig_EARLY(database_url=_dbos_db_url_early, name=_app_name_early)
        _DBOS_EARLY(config=_cfg_early)
        logging.getLogger(__name__).info("✅ DBOS pre-initialized (no framework binding yet)")
    except Exception as _e:
        logging.getLogger(__name__).warning(f"DBOS pre-init skipped: {_e}")
else:
    logging.getLogger(__name__).info("⏭️  DBOS pre-init skipped (test mode)")

from workflow_engine_poc.routers import (
    a2a_agents,
    agents,
    executions,
    files,
    health,
    messages,
    monitoring as monitoring_router,
    prompts,
    steps,
    tools,
    workflows,
)
from workflow_engine_poc.routers.approvals import router as approvals
from workflow_engine_poc.tenant_admin import tenant_admin_router, validate_tenant_exists


ElevaiteLogger.attach_to_uvicorn(
    service_name="workflow-engine",
    configure_otel=True,
    otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
    resource_attributes={
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    },
)  # OTEL


# Configure logging (honor LOG_LEVEL env, default INFO)
_LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
_NUM_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
logging.basicConfig(level=_NUM_LEVEL)
logger = logging.getLogger(__name__)
logger.setLevel(_NUM_LEVEL)
# Raise level on our internal loggers as well
for _name in [
    "workflow_engine_poc",
    "workflow_engine_poc.dbos_impl",
    "workflow_engine_poc.workflow_engine",
    "workflow_engine_poc.routers.messages",
    "workflow_engine_poc.steps.ai_steps",
]:
    logging.getLogger(_name).setLevel(_NUM_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Workflow Execution Engine PoC")

    # Initialize database
    # Ensure all SQLModel tables are registered before create_all by importing models
    try:
        from workflow_engine_poc.db import models as _wf_models  # noqa: F401  # side-effect import
    except Exception as _e:
        logger.warning(f"DB models import warning (continuing): {_e}")

    # Initialize tenant schemas for multitenancy
    try:
        logger.info(f"Initializing tenant schemas for: {DEFAULT_TENANTS}")
        initialize_tenant_db(
            settings=multitenancy_settings,
            tenant_ids=DEFAULT_TENANTS,
        )
        logger.info("✅ Tenant schemas initialized")

        # Initialize tenant cache with default tenants
        from db_core import get_tenant_cache

        tenant_cache = get_tenant_cache()
        tenant_cache.refresh(set(DEFAULT_TENANTS))
        logger.info(f"✅ Tenant cache initialized with {len(DEFAULT_TENANTS)} tenants")
    except Exception as e:
        logger.error(f"Failed to initialize tenant schemas: {e}")
        # Fall back to non-tenant database initialization
        create_db_and_tables()
        logger.warning("⚠️  Falling back to non-tenant database mode")

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

    # Launch DBOS executor if configured (skip in test mode)
    if not os.getenv("TESTING"):
        try:
            from dbos import DBOS as _DBOS_CLASS

            _DBOS_CLASS.launch()
            logger.info("✅ DBOS executor launched")
        except Exception as e:
            logger.warning(f"DBOS launch skipped/failed: {e}")
    else:
        logger.info("⏭️  DBOS executor skipped (test mode)")

    # Start lightweight scheduler (interval mode only for now)
    try:
        from workflow_engine_poc.scheduler import WorkflowScheduler

        scheduler = WorkflowScheduler(poll_interval_seconds=int(os.getenv("SCHEDULER_POLL_SECONDS", "15")))
        app.state.scheduler = scheduler
        await scheduler.start(app)
    except Exception as e:
        logger.warning(f"Scheduler start failed: {e}")

    yield

    logger.info("🛑 Shutting down Workflow Execution Engine")
    try:
        if getattr(app.state, "scheduler", None):
            await app.state.scheduler.stop()
    except Exception:
        pass


# Create FastAPI app
app = FastAPI(
    title="Unified Workflow Execution Engine",
    description="A clean, agnostic workflow execution engine PoC",
    version="1.0.0-poc",
    lifespan=lifespan,
)

# Add tenant middleware for multitenancy
# Excluded paths don't require tenant ID header
excluded_paths = {
    r"^/health$": {"default_tenant": "default"},
    r"^/docs.*": {"default_tenant": "default"},
    r"^/redoc.*": {"default_tenant": "default"},
    r"^/openapi\.json$": {"default_tenant": "default"},
    r"^/admin/tenants.*": {"default_tenant": "default"},  # Tenant admin endpoints
}
add_tenant_middleware(
    app,
    settings=multitenancy_settings,
    tenant_callback=validate_tenant_exists,  # Validate tenant exists and is active
    excluded_paths=excluded_paths,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)  # OTEL

# Include all routers
app.include_router(health)
app.include_router(workflows)
app.include_router(executions)
app.include_router(steps)
app.include_router(files)
app.include_router(monitoring_router)
app.include_router(agents)
app.include_router(a2a_agents)
app.include_router(tools)
app.include_router(prompts)
app.include_router(messages)
app.include_router(approvals)
app.include_router(tenant_admin_router, prefix="/admin")

# Initialize DBOS context if available so DBOS.start_* can be used (skip in test mode)
if not os.getenv("TESTING"):
    try:  # Lazy import so dev env without DBOS package still runs
        from dbos import DBOS as _DBOS, DBOSConfig as _DBOSConfig

        # Reuse engine DB URL if explicit DBOS vars are not set
        from workflow_engine_poc.db.database import DATABASE_URL as _ENGINE_DB_URL

        # Prefer explicit DBOS_DATABASE_URL, then DATABASE_URL; fallback to engine DB URL
        _dbos_db_url = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL

        _app_name = os.getenv("DBOS_APPLICATION_NAME") or "workflow-engine-poc"
        _cfg = _DBOSConfig(database_url=_dbos_db_url, name=_app_name)
        _dbos_inst = _DBOS(config=_cfg, fastapi=app)
        app.state.dbos = _dbos_inst
        logging.getLogger(__name__).info("✅ DBOS initialized for %s (app=%s)", _dbos_db_url, _app_name)
    except Exception as _e:  # pragma: no cover - optional dependency
        logging.getLogger(__name__).warning(f"DBOS not initialized: {_e}")
else:
    logging.getLogger(__name__).info("⏭️  DBOS initialization skipped (test mode)")


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
