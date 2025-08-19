"""
Database Service for Workflow Engine

Provides database operations using db-core patterns with SQLAlchemy models.
Supports both PostgreSQL (production) and in-memory (development/testing).
"""

import json
import asyncio
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import db-core components with graceful fallback
try:
    from db_core import init_db, get_tenant_async_session, Base
    from db_core.config import MultitenancySettings

    DB_CORE_AVAILABLE = True
except ImportError:
    logger.warning("db-core not available, using simple database implementation")
    DB_CORE_AVAILABLE = False
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

# Import database models
from .db_models import (
    WorkflowConfig,
    StepRegistration,
    WorkflowExecution,
    StepExecution,
    AgentConfig,
    ToolConfig,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Database service for the workflow engine.

    Provides async database operations using SQLAlchemy models and db-core patterns.
    Supports both PostgreSQL (production) and SQLite (development/testing).
    """

    def __init__(
        self, database_url: Optional[str] = None, use_multitenancy: bool = False
    ):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./workflow_engine.db"
        )
        self.use_multitenancy = use_multitenancy
        self.engine = None
        self.session_factory = None
        self.multitenancy_settings = None

        # Fallback in-memory storage for when database is not available
        self.workflows = {}
        self.agents = {}
        self.tools = {}
        self.step_configs = {}
        self.execution_contexts = {}
        self.execution_history = []
        self.use_fallback = False

        # For compatibility with old methods
        self.persist_to_file = False
        self.data_dir = Path("data")

    async def init_database(self):
        """Initialize the database connection and create tables"""
        try:
            if DB_CORE_AVAILABLE and self.use_multitenancy:
                await self._init_with_db_core()
            else:
                await self._init_simple_async()

            logger.info(
                f"Database initialized successfully with URL: {self.database_url}"
            )

        except Exception as e:
            logger.warning(
                f"Database initialization failed: {e}, falling back to in-memory storage"
            )
            self.use_fallback = True

    async def _init_with_db_core(self):
        """Initialize database using db-core for multitenancy"""
        self.multitenancy_settings = MultitenancySettings()

        # Initialize database with db-core
        db_config = init_db(
            settings=self.multitenancy_settings,
            db_url=self.database_url,
            is_async=True,
            base_model_class=Base,
        )

        self.engine = db_config["engine"]
        self.session_factory = db_config["session_factory"]

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _init_simple_async(self):
        """Initialize database with simple async SQLAlchemy"""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
        )

        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self):
        """Get a database session"""
        if self.use_fallback:
            # Return a mock session for fallback mode
            yield None
            return

        if self.use_multitenancy and DB_CORE_AVAILABLE:
            session = await get_tenant_async_session(self.multitenancy_settings)
        else:
            session = self.session_factory()

        try:
            yield session
        finally:
            if session:
                await session.close()

    async def _load_from_files(self):
        """Load data from JSON files"""
        try:
            files_to_load = [
                ("workflows.json", self.workflows),
                ("agents.json", self.agents),
                ("tools.json", self.tools),
                ("step_configs.json", self.step_configs),
                ("execution_contexts.json", self.execution_contexts),
                ("execution_history.json", self.execution_history),
            ]

            for filename, storage in files_to_load:
                file_path = self.data_dir / filename
                if file_path.exists():
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        if isinstance(storage, dict):
                            storage.update(data)
                        elif isinstance(storage, list):
                            storage.extend(data)
                    logger.info(f"Loaded {filename}")

        except Exception as e:
            logger.warning(f"Failed to load persisted data: {e}")

    async def _save_to_files(self):
        """Save data to JSON files"""
        if not self.persist_to_file:
            return

        try:
            files_to_save = [
                ("workflows.json", self.workflows),
                ("agents.json", self.agents),
                ("tools.json", self.tools),
                ("step_configs.json", self.step_configs),
                ("execution_contexts.json", self.execution_contexts),
                ("execution_history.json", self.execution_history),
            ]

            for filename, data in files_to_save:
                file_path = self.data_dir / filename
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save data to files: {e}")

    # Workflow operations
    async def save_workflow(
        self, workflow_id: str, workflow_data: Dict[str, Any]
    ) -> str:
        """Save a workflow configuration"""
        workflow_data["workflow_id"] = workflow_id
        workflow_data["updated_at"] = datetime.now().isoformat()

        if "created_at" not in workflow_data:
            workflow_data["created_at"] = workflow_data["updated_at"]

        self.workflows[workflow_id] = workflow_data
        await self._save_to_files()

        return workflow_id

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)

    async def list_workflows(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List workflows with pagination"""
        workflows = list(self.workflows.values())
        return workflows[offset : offset + limit]

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            await self._save_to_files()
            return True
        return False

    # Agent operations
    async def save_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> str:
        """Save an agent configuration"""
        agent_data["agent_id"] = agent_id
        agent_data["updated_at"] = datetime.now().isoformat()

        if "created_at" not in agent_data:
            agent_data["created_at"] = agent_data["updated_at"]

        self.agents[agent_id] = agent_data
        await self._save_to_files()

        return agent_id

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)

    async def list_agents(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List agents with pagination"""
        agents = list(self.agents.values())
        return agents[offset : offset + limit]

    # Step configuration operations
    async def save_step_config(self, step_id: str, step_data: Dict[str, Any]) -> str:
        """Save a step configuration"""
        step_data["step_id"] = step_id
        step_data["updated_at"] = datetime.now().isoformat()

        if "created_at" not in step_data:
            step_data["created_at"] = step_data["updated_at"]

        self.step_configs[step_id] = step_data
        await self._save_to_files()

        return step_id

    async def get_step_config(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get a step configuration by ID"""
        return self.step_configs.get(step_id)

    async def list_step_configs(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List step configurations with pagination"""
        configs = list(self.step_configs.values())
        return configs[offset : offset + limit]

    # Execution context operations
    async def save_execution_context(
        self, execution_id: str, context_data: Dict[str, Any]
    ) -> str:
        """Save an execution context"""
        context_data["execution_id"] = execution_id
        context_data["updated_at"] = datetime.now().isoformat()

        if "created_at" not in context_data:
            context_data["created_at"] = context_data["updated_at"]

        self.execution_contexts[execution_id] = context_data
        await self._save_to_files()

        return execution_id

    async def get_execution_context(
        self, execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get an execution context by ID"""
        return self.execution_contexts.get(execution_id)

    async def list_execution_contexts(
        self, limit: int = 100, offset: int = 0, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List execution contexts with pagination and filtering"""
        contexts = list(self.execution_contexts.values())

        # Filter by status if provided
        if status:
            contexts = [ctx for ctx in contexts if ctx.get("status") == status]

        # Sort by creation time (most recent first)
        contexts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return contexts[offset : offset + limit]

    async def archive_execution_context(self, execution_id: str) -> bool:
        """Move an execution context to history"""
        if execution_id in self.execution_contexts:
            context = self.execution_contexts[execution_id]
            context["archived_at"] = datetime.now().isoformat()

            self.execution_history.append(context)
            del self.execution_contexts[execution_id]

            # Keep only recent history (last 1000 executions)
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]

            await self._save_to_files()
            return True

        return False

    # Tool operations
    async def save_tool(self, tool_id: str, tool_data: Dict[str, Any]) -> str:
        """Save a tool configuration"""
        tool_data["tool_id"] = tool_id
        tool_data["updated_at"] = datetime.now().isoformat()

        if "created_at" not in tool_data:
            tool_data["created_at"] = tool_data["updated_at"]

        self.tools[tool_id] = tool_data
        await self._save_to_files()

        return tool_id

    async def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a tool by ID"""
        return self.tools.get(tool_id)

    async def list_tools(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tools with pagination"""
        tools = list(self.tools.values())
        return tools[offset : offset + limit]

    # Analytics operations
    async def get_execution_analytics(
        self, limit: int = 100, offset: int = 0, status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get execution analytics"""

        # Combine active and historical executions
        all_executions = list(self.execution_contexts.values()) + self.execution_history

        # Filter by status if provided
        if status:
            all_executions = [
                exec_ctx
                for exec_ctx in all_executions
                if exec_ctx.get("status") == status
            ]

        # Sort by creation time (most recent first)
        all_executions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Paginate
        total = len(all_executions)
        paginated = all_executions[offset : offset + limit]

        # Generate statistics
        status_counts = {}
        for exec_ctx in all_executions:
            status = exec_ctx.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_executions": total,
            "executions": paginated,
            "statistics": {
                "status_distribution": status_counts,
                "active_executions": len(self.execution_contexts),
                "archived_executions": len(self.execution_history),
            },
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "has_more": offset + limit < total,
            },
        }


# Global database instance
_database = None


async def get_database() -> DatabaseService:
    """Get the global database instance"""
    global _database
    if _database is None:
        _database = DatabaseService()
        await _database.init_database()
    return _database


async def init_database():
    """Initialize the global database"""
    await get_database()


# Test function
async def test_database():
    """Test the database functionality"""

    db = await get_database()

    print("Testing Database Operations:")
    print("=" * 50)

    # Test workflow operations
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "steps": [{"step_id": "step1", "step_type": "data_input"}],
    }

    workflow_id = "test-workflow-123"
    await db.save_workflow(workflow_id, workflow_data)

    retrieved = await db.get_workflow(workflow_id)
    print(f"Saved and retrieved workflow: {retrieved['name']}")

    # Test agent operations
    agent_data = {
        "name": "Test Agent",
        "model": "gpt-4o-mini",
        "system_prompt": "You are a test agent",
    }

    agent_id = "test-agent-123"
    await db.save_agent(agent_id, agent_data)

    retrieved_agent = await db.get_agent(agent_id)
    print(f"Saved and retrieved agent: {retrieved_agent['name']}")

    print("✅ Database test completed!")


# Global database instance
database = DatabaseService()


if __name__ == "__main__":
    asyncio.run(test_database())
