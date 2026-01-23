"""
Unified Workflow Execution Engine - FastAPI PoC

A clean, agnostic workflow execution engine built on workflow-core-sdk.
Includes full multitenancy support with tenant administration.
"""

import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Import core components from the SDK
from workflow_core_sdk import (
    StepRegistry,
    WorkflowEngine,
    create_db_and_tables,
    tool_registry,
)

# Multitenancy support
from db_core.middleware import add_tenant_middleware
from db_core import get_tenant_cache
from workflow_core_sdk.multitenancy import multitenancy_settings, DEFAULT_TENANTS
from workflow_core_sdk.db.tenant_db import initialize_tenant_db

# Import routers from local PoC code
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
from workflow_engine_poc.tenant_admin import (
    tenant_admin_router,
    validate_tenant_exists,
    get_admin_session,
    get_tenant_registry,
)

from fastapi_logger import ElevaiteLogger

# Early DBOS bootstrap
try:
    from dbos import DBOS as _DBOS_EARLY, DBOSConfig as _DBOSConfig_EARLY
    from workflow_core_sdk.db.database import DATABASE_URL as _ENGINE_DB_URL

    _dbos_db_url_early = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL
    _app_name_early = os.getenv("DBOS_APPLICATION_NAME") or "workflow-engine-poc-sdk"
    _app_version_early = os.getenv("DBOS_APPLICATION_VERSION")  # Fixed version for recovery
    _cfg_early: _DBOSConfig_EARLY = {
        "name": _app_name_early,
        "system_database_url": _dbos_db_url_early,
    }
    if _app_version_early:
        _cfg_early["application_version"] = _app_version_early
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
    """Application lifespan management - SDK version with multitenancy"""
    logger.info("=" * 70)
    logger.info("🚀 Workflow Engine PoC - Running on workflow-core-sdk")
    logger.info("=" * 70)

    # Initialize tenant schemas for multitenancy
    try:
        logger.info(f"Initializing tenant schemas for: {DEFAULT_TENANTS}")
        initialize_tenant_db(
            settings=multitenancy_settings,
            tenant_ids=DEFAULT_TENANTS,
        )
        logger.info("✅ Tenant schemas initialized (SDK)")

        # Ensure the _tenants registry table exists in public schema
        async for session in get_admin_session():
            registry = get_tenant_registry()
            await registry.ensure_tenant_table(session)
            logger.info("✅ Tenant registry table ensured")
            break

        # Initialize tenant cache with default tenants
        tenant_cache = get_tenant_cache()
        tenant_cache.refresh(set(DEFAULT_TENANTS))
        logger.info(f"✅ Tenant cache initialized with {len(DEFAULT_TENANTS)} tenants")
    except Exception as e:
        logger.error(f"Failed to initialize tenant schemas: {e}")
        logger.warning("⚠️  Falling back to non-tenant database mode")

    # ALWAYS create tables in public schema for scheduler (it queries without tenant context)
    create_db_and_tables()
    logger.info("✅ Public schema tables ensured (for scheduler)")

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

    # Launch DBOS executor if configured (skip in test mode)
    if not os.getenv("TESTING"):
        logger.info("Launching DBOS executor...")
        try:
            from dbos import DBOS as _DBOS_CLASS

            _DBOS_CLASS.launch()
            logger.info("✅ DBOS executor launched (SDK)")
        except Exception as e:
            # DBOS tables may already exist from early initialization - this is expected
            error_msg = str(e)
            if "already exists" in error_msg or "DuplicateTable" in error_msg:
                logger.debug(f"DBOS already initialized (tables exist): {error_msg}")
                logger.info("✅ DBOS executor ready (already initialized)")
            else:
                logger.warning(f"DBOS launch skipped/failed: {e}")
    else:
        logger.info("⏭️  DBOS executor skipped (test mode)")

    # Start scheduler if available (skip in test mode to avoid cleanup issues)
    if not os.getenv("TESTING"):
        try:
            from workflow_core_sdk.scheduler import WorkflowScheduler

            scheduler = WorkflowScheduler(poll_interval_seconds=int(os.getenv("SCHEDULER_POLL_SECONDS", "15")))
            app.state.scheduler = scheduler
            await scheduler.start(app)
            logger.info("✅ Scheduler started (SDK)")
        except Exception as e:
            logger.warning(f"Scheduler start skipped/failed: {e}")
    else:
        logger.info("⏭️  Scheduler skipped (test mode)")

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
    title="Unified Workflow Execution Engine",
    description="A clean, agnostic workflow execution engine with multitenancy support",
    version="2.0.0",
    lifespan=lifespan,
)

# Add tenant middleware for multitenancy
# Excluded paths don't require tenant ID header
excluded_paths = {
    r"^/$": {"default_tenant": "default"},
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

# Include all routers at root (backwards-compat)
app.include_router(health)
app.include_router(workflows)
app.include_router(executions)
app.include_router(agents)
app.include_router(a2a_agents)
app.include_router(tools)
app.include_router(steps)
app.include_router(files)
app.include_router(messages)
app.include_router(prompts)
app.include_router(approvals)
app.include_router(monitoring_router)
app.include_router(tenant_admin_router, prefix="/admin")

# Also expose the same routes under /api for clients expecting that prefix
api_router = APIRouter(prefix="/api")
api_router.include_router(health)
api_router.include_router(workflows)
api_router.include_router(executions)
api_router.include_router(steps)
api_router.include_router(files)
api_router.include_router(monitoring_router)
api_router.include_router(agents)
api_router.include_router(tools)
api_router.include_router(prompts)
api_router.include_router(messages)
api_router.include_router(approvals)
app.include_router(api_router)

# Initialize DBOS context if available (skip in test mode)
if not os.getenv("TESTING"):
    try:
        from dbos import DBOS as _DBOS, DBOSConfig as _DBOSConfig
        from workflow_core_sdk.db.database import DATABASE_URL as _ENGINE_DB_URL

        _dbos_db_url = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL
        _app_name = os.getenv("DBOS_APPLICATION_NAME") or "workflow-engine-poc-sdk"
        _app_version = os.getenv("DBOS_APPLICATION_VERSION")  # Fixed version for recovery
        _cfg: _DBOSConfig = {
            "name": _app_name,
            "system_database_url": _dbos_db_url,
        }
        if _app_version:
            _cfg["application_version"] = _app_version
        _dbos_inst = _DBOS(config=_cfg, fastapi=app)
        app.state.dbos = _dbos_inst
        logger.info(f"✅ DBOS initialized for {_dbos_db_url} (app={_app_name}, version={_app_version or 'auto'})")
    except Exception as _e:
        logger.warning(f"DBOS not initialized: {_e}")
else:
    logger.info("⏭️  DBOS initialization skipped (test mode)")


if __name__ == "__main__":
    uvicorn.run(
        "workflow_engine_poc.main:app",
        host="0.0.0.0",
        port=8006,
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
            ".git/*",  # Exclude git internals
            "logs/*",
            "data/*",
            "*.json",
            "*/node_modules/*",
        ],
    )
