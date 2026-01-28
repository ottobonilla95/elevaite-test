"""
Background Tasks Service for Agent Studio

This module manages background tasks including MCP server health monitoring,
tool synchronization, and other periodic maintenance tasks.

Phase 2: MCP health monitoring and maintenance
"""

import asyncio
import logging
from contextlib import asynccontextmanager

# MCP imports are done locally to avoid circular imports

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manager for background tasks in Agent Studio.

    Handles starting and stopping of background services like
    MCP health monitoring, tool synchronization, etc.
    """

    def __init__(self):
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def start_all_tasks(self):
        """Start all background tasks."""
        if self._running:
            logger.warning("Background tasks are already running")
            return

        self._running = True
        logger.info("Starting background tasks...")

        # Start MCP health monitoring (non-blocking)
        try:
            await self._start_mcp_health_monitoring()
            logger.info("MCP health monitoring started successfully")
        except Exception as e:
            logger.error(f"Failed to start MCP health monitoring: {e}")
            # Don't fail the entire startup for this

        # Add other background tasks here as needed
        # await self._start_tool_synchronization()
        # await self._start_analytics_aggregation()

        logger.info(f"Background task startup completed. Running tasks: {len(self._tasks)}")

    async def stop_all_tasks(self):
        """Stop all background tasks."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping background tasks...")

        # Stop MCP health monitoring
        try:
            from services.mcp_client import mcp_health_monitor

            await mcp_health_monitor.stop_monitoring()
        except ImportError:
            logger.warning("Could not import MCP health monitor for shutdown")
        except Exception as e:
            logger.error(f"Error stopping MCP health monitor: {e}")

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()
        logger.info("All background tasks stopped")

    async def _start_mcp_health_monitoring(self):
        """Start MCP server health monitoring."""
        try:
            # Import here to avoid circular imports
            from services.mcp_client import mcp_health_monitor
            from db.database import SessionLocal

            # Create a database session factory
            def get_db_session():
                return SessionLocal()

            # Start the health monitoring
            await mcp_health_monitor.start_monitoring(get_db_session)
            logger.info("MCP health monitoring started")

        except ImportError as e:
            logger.warning(f"Could not import MCP components: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to start MCP health monitoring: {e}")
            raise

    async def _start_tool_synchronization(self):
        """Start tool synchronization task (placeholder for future implementation)."""
        # This could be used to periodically sync tools from MCP servers
        # or perform other tool-related maintenance tasks
        pass

    async def _start_analytics_aggregation(self):
        """Start analytics aggregation task (placeholder for future implementation)."""
        # This could be used to aggregate usage statistics,
        # performance metrics, etc.
        pass

    @property
    def is_running(self) -> bool:
        """Check if background tasks are running."""
        return self._running

    def get_task_status(self) -> dict:
        """Get status of all background tasks."""
        return {
            "running": self._running,
            "task_count": len(self._tasks),
            "tasks": [
                {
                    "name": task.get_name() if hasattr(task, "get_name") else str(task),
                    "done": task.done(),
                    "cancelled": task.cancelled(),
                }
                for task in self._tasks
            ],
        }


# Global background task manager
background_task_manager = BackgroundTaskManager()


@asynccontextmanager
async def lifespan_context():
    """
    Context manager for application lifespan.

    Starts background tasks on startup and stops them on shutdown.
    This can be used with FastAPI's lifespan parameter.
    """
    try:
        # Startup
        await background_task_manager.start_all_tasks()
        yield
    finally:
        # Shutdown
        await background_task_manager.stop_all_tasks()


async def start_background_tasks():
    """Start all background tasks. Can be called manually if needed."""
    await background_task_manager.start_all_tasks()


async def stop_background_tasks():
    """Stop all background tasks. Can be called manually if needed."""
    await background_task_manager.stop_all_tasks()


def get_background_task_status() -> dict:
    """Get the status of background tasks."""
    return background_task_manager.get_task_status()


# Health check function for background tasks
async def health_check_background_tasks() -> dict:
    """
    Perform health check on background tasks.

    Returns:
        Dictionary with health status information
    """
    status = background_task_manager.get_task_status()

    # Check if critical tasks are running
    is_healthy = status["running"] and status["task_count"] > 0

    # Check for failed tasks
    failed_tasks = [task for task in status["tasks"] if task["done"] and not task["cancelled"]]

    if failed_tasks:
        is_healthy = False

    return {
        "healthy": is_healthy,
        "status": status,
        "failed_tasks": failed_tasks,
        "message": "Background tasks are healthy" if is_healthy else "Some background tasks have issues",
    }


# Utility functions for specific background tasks
async def trigger_mcp_health_check():
    """Manually trigger MCP health check for all servers."""
    try:
        from services.mcp_client import mcp_client
        from db.database import SessionLocal
        from db import crud

        db = SessionLocal()
        try:
            servers = crud.get_mcp_servers(db, skip=0, limit=1000)
            results = []

            for server in servers:
                try:
                    is_healthy = await mcp_client.health_check(server)
                    crud.update_mcp_server_health(db, server.server_id, is_healthy)
                    results.append({"server_id": str(server.server_id), "name": server.name, "healthy": is_healthy})
                except Exception as e:
                    logger.error(f"Health check failed for server {server.name}: {e}")
                    results.append({"server_id": str(server.server_id), "name": server.name, "healthy": False, "error": str(e)})

            return {"success": True, "checked_servers": len(results), "results": results}

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Manual health check failed: {e}")
        return {"success": False, "error": str(e)}


async def sync_tools_from_mcp_servers():
    """Manually trigger tool synchronization from all MCP servers."""
    try:
        from services.mcp_client import mcp_client
        from db.database import SessionLocal
        from db import crud

        db = SessionLocal()
        try:
            servers = crud.get_active_mcp_servers(db)
            results = []

            for server in servers:
                try:
                    tools = await mcp_client.register_tools_from_server(server, db)
                    results.append(
                        {
                            "server_id": str(server.server_id),
                            "name": server.name,
                            "tools_registered": len(tools),
                            "success": True,
                        }
                    )
                except Exception as e:
                    logger.error(f"Tool sync failed for server {server.name}: {e}")
                    results.append({"server_id": str(server.server_id), "name": server.name, "success": False, "error": str(e)})

            return {"success": True, "synced_servers": len(results), "results": results}

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Manual tool sync failed: {e}")
        return {"success": False, "error": str(e)}
