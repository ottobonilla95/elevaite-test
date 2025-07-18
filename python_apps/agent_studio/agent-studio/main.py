import os
import uuid
import dotenv
import fastapi
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware
from fastapi import Depends
from sqlalchemy.orm import Session

from services.analytics_service import analytics_service
from db.database import Base, engine, get_db
from api import prompt_router, agent_router, demo_router, analytics_router, tools_router
from api.workflow_endpoints import router as workflow_router
from db import crud

# Temporarily comment out workflow service to test
# from services.workflow_service import workflow_service

from contextlib import asynccontextmanager
from services.shared_state import session_status, update_status, get_status
from fastapi.responses import StreamingResponse
import logging
import asyncio

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

    # Initialize tool registry
    from services.tool_registry import tool_registry
    try:
        # Get a database session for initialization
        db_gen = get_db()
        db = next(db_gen)
        try:
            tool_registry.initialize(db)
            logging.info("Tool registry initialized successfully")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Failed to initialize tool registry: {e}")
        raise
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(prompt_router)
app.include_router(agent_router)
app.include_router(demo_router)
app.include_router(analytics_router)
app.include_router(workflow_router)
app.include_router(tools_router)


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
    """
    available_agents = crud.get_available_agents(db)

    code_map = {}
    for agent in available_agents:
        deployment_code = getattr(agent, "deployment_code", None)
        if deployment_code is not None and str(deployment_code).strip() != "":
            code_map[str(deployment_code)] = str(agent.name)

    return code_map


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
        results["prompts"] = {"success": prompts_success, "message": prompts_message, "details": prompts_details}

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

            total_categories = crud.get_tool_categories(db)
            total_tools = crud.get_tools(db)
            tools_message = f"Initialized {len(total_categories)} categories and {len(total_tools)} tools"

            results["tools"] = {
                "success": True,
                "message": tools_message,
                "details": {"categories": len(total_categories), "tools": len(total_tools)},
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
                results["agents"] = {"success": agents_success, "message": agents_message, "details": agents_details}

                if agents_success:
                    print(f"✅ Agents: {agents_message}")
                else:
                    print(f"❌ Agents: {agents_message}")
                    overall_success = False

            except Exception as e:
                agents_error = f"Agent initialization failed: {str(e)}"
                results["agents"] = {"success": False, "message": agents_error, "details": {}}
                print(f"❌ Agents: {agents_error}")
                overall_success = False
        else:
            skip_message = "Skipped agent initialization due to prompt initialization failure"
            results["agents"] = {"success": False, "message": skip_message, "details": {}}
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
        allow_headers=["Content-Type", "Authorization"],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)
