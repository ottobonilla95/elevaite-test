import os
import dotenv
import fastapi
import asyncio
import logging
from starlette.middleware.cors import CORSMiddleware
from fastapi import Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from services.shared_state import session_status, update_status, get_status
from fastapi.responses import StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from fastapi_logger import ElevaiteLogger

from db.database import Base, engine, get_db
from api import (
    prompt_router,
    agent_router,
    # demo_router,
    analytics_router,
    tools_router,
    file_router,
)
from api.workflow_endpoints import router as workflow_router
from api.execution_endpoints import router as execution_router
from api.pipeline_endpoints import router as pipeline_router
from api.step_endpoints import router as step_router

# Use SDK services instead of old crud module
from workflow_core_sdk.services.tools_service import ToolsService

# Temporarily comment out workflow service to test
# from services.workflow_service import workflow_service


# Initialize ElevaiteLogger and OpenTelemetry provider (if configured)
try:
    ElevaiteLogger.attach_to_uvicorn(
        service_name="agent-studio",
        configure_otel=True,
        otlp_endpoint=os.getenv("OTLP_ENDPOINT"),
        resource_attributes={
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        },
    )
except Exception as e:
    pass


# Configure logging with a custom filter to suppress CancelledError
class CancelledErrorFilter(logging.Filter):
    def filter(self, record):
        # Filter out CancelledError exceptions from asyncio
        if record.exc_info and record.exc_info[0] is asyncio.CancelledError:
            return False
        # Also filter out log messages that contain "CancelledError"
        if "CancelledError" in record.getMessage():
            return False
        return True


# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)

# Add the filter to the root logger
root_logger = logging.getLogger()
cancelled_error_filter = CancelledErrorFilter()
for handler in root_logger.handlers:
    handler.addFilter(cancelled_error_filter)


# Set up custom exception handler for asyncio to suppress CancelledError
def custom_exception_handler(loop, context):
    """Custom exception handler for asyncio that suppresses CancelledError."""
    exception = context.get("exception")
    if isinstance(exception, asyncio.CancelledError):
        # Silently ignore CancelledError exceptions
        return

    # For other exceptions, use the default handler
    loop.default_exception_handler(context)


# Set the custom exception handler for the current event loop
try:
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(custom_exception_handler)
except RuntimeError:
    # If no event loop is running, we'll set it later when the loop starts
    pass

dotenv.load_dotenv(".env.local")

CX_ID = os.getenv("CX_ID_PERSONAL")
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")


origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "*",  # Allow all origins for development
]


@asynccontextmanager
async def lifespan(app_instance: fastapi.FastAPI):  # noqa: ARG001
    # Startup
    # Ensure the custom exception handler is set for the current event loop
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(custom_exception_handler)
    except RuntimeError:
        pass

    Base.metadata.create_all(bind=engine)
    # Note: Database initialization moved to /admin/initialize endpoint

    # Sync local tools to database so they get IDs
    from workflow_core_sdk.tools.registry import tool_registry

    try:
        # Get a database session for syncing
        db_gen = get_db()
        db = next(db_gen)
        try:
            sync_result = tool_registry.sync_local_to_db(db)
            logging.info(f"✅ Synced local tools to database: {sync_result}")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Failed to sync local tools to database: {e}")
        # Continue startup even if sync fails

    # Note: Old agent-studio tool_registry removed - using SDK's tool_registry instead
    # The SDK tool_registry is used by tool_endpoints.py and agent_endpoints.py

    # Initialize workflow execution engine
    from workflow_core_sdk.execution.registry_impl import StepRegistry
    from workflow_core_sdk.execution.engine_impl import WorkflowEngine

    try:
        step_registry = StepRegistry()
        await step_registry.register_builtin_steps()
        workflow_engine = WorkflowEngine(step_registry)

        # Store in app state for use by endpoints
        app_instance.state.step_registry = step_registry
        app_instance.state.workflow_engine = workflow_engine

        logging.info("✅ Workflow execution engine initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize workflow execution engine: {e}")
        # Don't raise - allow app to start even if execution engine fails
        # Execution endpoints will return 503 if engine is not available

    # Agent execution step is now registered automatically in workflow_execution_context initialization
    # Start background tasks (MCP health monitoring, etc.)
    from services.background_tasks import start_background_tasks

    try:
        await start_background_tasks()
        logging.info("Background tasks started successfully")
    except Exception as e:
        logging.error(f"Failed to start background tasks: {e}")
        # Continue startup even if background tasks fail

    yield

    # Shutdown
    from services.background_tasks import stop_background_tasks

    try:
        await stop_background_tasks()
        logging.info("Background tasks stopped successfully")
    except Exception as e:
        logging.error(f"Error stopping background tasks: {e}")

    # Close MCP client connections
    from services.mcp_client import mcp_client

    try:
        await mcp_client.close()
        logging.info("MCP client connections closed")
    except Exception as e:
        logging.error(f"Error closing MCP client: {e}")


app = fastapi.FastAPI(title="Agent Studio Backend", version="0.1.0", lifespan=lifespan)

FastAPIInstrumentor.instrument_app(app)  # OTEL

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Cache-Control",
        "Accept",
        "Accept-Encoding",
        "Accept-Language",
    ],
)

app.include_router(prompt_router)
app.include_router(agent_router)
# app.include_router(demo_router)  # Commented out - not imported
app.include_router(analytics_router)
app.include_router(workflow_router)
app.include_router(execution_router)
app.include_router(tools_router)
app.include_router(file_router)
app.include_router(pipeline_router)
app.include_router(step_router)


@app.get("/")
def status():
    return {"status": "ok"}


@app.get("/hc")
async def health_check():
    """Enhanced health check including background tasks."""
    from services.background_tasks import health_check_background_tasks

    basic_status = {"status": "ok"}

    try:
        background_status = await health_check_background_tasks()
        return {**basic_status, "background_tasks": background_status}
    except Exception as e:
        return {**basic_status, "background_tasks": {"healthy": False, "error": str(e)}}


@app.get("/deployment/codes")
def get_deployment_codes(db: Session = fastapi.Depends(get_db)):
    """
    Get a mapping of deployment codes to agent names.
    This endpoint is used by the frontend to display available agents.

    STUBBED: Old deployment_code field doesn't exist in SDK schema.
    """
    # TODO: Implement using SDK's AgentsService if deployment codes are needed
    # For now, return empty dict to keep frontend working
    return {}


@app.post("/admin/initialize")
async def initialize_system(db: Session = Depends(get_db)):
    """Initialize the complete system: prompts, tools, and agents in the correct order."""
    try:
        from db.init_db import init_tool_categories, init_tools
        from services.demo_service import DemoInitializationService

        results = {}
        overall_success = True

        print("🚀 Starting system initialization...")

        # Step 1: Initialize prompts first (required for agents)
        print("📋 Step 1: Initializing prompts...")
        service = DemoInitializationService(db)
        prompts_success, prompts_message, prompts_details = service.initialize_prompts()
        results["prompts"] = {
            "success": prompts_success,
            "message": prompts_message,
            "details": prompts_details,
        }

        if prompts_success:
            print(f"✅ Prompts: {prompts_message}")
        else:
            print(f"❌ Prompts: {prompts_message}")
            overall_success = False

        # Step 2: Initialize tool categories and tools
        print("🛠️  Step 2: Initializing tools...")
        try:
            categories = init_tool_categories(db)
            init_tools(db, categories)

            # Use SDK services instead of old crud
            total_categories = ToolsService.list_categories(db)
            total_tools = ToolsService.list_db_tools(db)
            tools_message = f"Initialized {len(total_categories)} categories and {len(total_tools)} tools"

            results["tools"] = {
                "success": True,
                "message": tools_message,
                "details": {
                    "categories": len(total_categories),
                    "tools": len(total_tools),
                },
            }
            print(f"✅ Tools: {tools_message}")

        except Exception as e:
            tools_error = f"Tool initialization failed: {str(e)}"
            results["tools"] = {"success": False, "message": tools_error, "details": {}}
            print(f"❌ Tools: {tools_error}")
            overall_success = False

        # Step 3: Initialize agents (requires prompts to exist)
        print("🤖 Step 3: Initializing agents...")
        if prompts_success:
            try:
                agents_success, agents_message, agents_details = service.initialize_agents()
                results["agents"] = {
                    "success": agents_success,
                    "message": agents_message,
                    "details": agents_details,
                }

                if agents_success:
                    print(f"✅ Agents: {agents_message}")
                else:
                    print(f"❌ Agents: {agents_message}")
                    overall_success = False

            except Exception as e:
                agents_error = f"Agent initialization failed: {str(e)}"
                results["agents"] = {
                    "success": False,
                    "message": agents_error,
                    "details": {},
                }
                print(f"❌ Agents: {agents_error}")
                overall_success = False
        else:
            skip_message = "Skipped agent initialization due to prompt initialization failure"
            results["agents"] = {
                "success": False,
                "message": skip_message,
                "details": {},
            }
            print(f"⏭️  Agents: {skip_message}")

        # Summary
        if overall_success:
            summary = "🎉 System initialization completed successfully!"
        else:
            summary = "⚠️  System initialization completed with some failures"

        print(summary)

        return {"success": overall_success, "message": summary, "results": results}

    except Exception as e:
        error_msg = f"System initialization failed: {str(e)}"
        print(f"💥 {error_msg}")
        return {"success": False, "error": error_msg}


@app.post("/admin/mcp/health-check")
async def trigger_mcp_health_check():
    """Manually trigger health check for all MCP servers."""
    from services.background_tasks import trigger_mcp_health_check

    try:
        result = await trigger_mcp_health_check()
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/admin/mcp/sync-tools")
async def sync_mcp_tools():
    """Manually trigger tool synchronization from all MCP servers."""
    from services.background_tasks import sync_tools_from_mcp_servers

    try:
        result = await sync_tools_from_mcp_servers()
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/admin/background-tasks/status")
async def get_background_task_status():
    """Get the status of background tasks."""
    from services.background_tasks import get_background_task_status

    try:
        return get_background_task_status()
    except Exception as e:
        return {"error": str(e)}


# Temporarily disable deploy endpoint to test API startup
# @app.post("/deploy")
# def deploy(request: dict, db: Session = fastapi.Depends(get_db)):
#     """
#     Modern workflow deployment endpoint - temporarily disabled
#     """
#     return {"status": "error", "message": "Deploy endpoint temporarily disabled"}
@app.get("/currentStatus")
async def get_current_status(uid: str, sid: str):
    """Endpoint to report real-time agent status updates based on actual processing."""
    print("uid", uid)
    print("sid", sid)
    print("session_status", session_status)

    async def status_generator():
        print("uid in generator", uid)
        print("sid in generator", sid)
        print("session_status", session_status)
        if uid not in session_status:
            update_status(uid, "Thinking...")
            yield f"data: Thinking...\n\n"

        last_status = None
        counter = 0
        while True:
            current_status = get_status(uid)
            counter += 1

            # Only send updates when status changes
            if current_status != last_status:
                yield f"data: {current_status}\n\n"
                last_status = current_status

            # Short polling interval
            await asyncio.sleep(0.1)

            # If status indicates completion, finish the stream
            if counter > 100:
                break

    return StreamingResponse(
        status_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Cache-Control",
            "Accept",
            "Accept-Encoding",
            "Accept-Language",
        ],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)
