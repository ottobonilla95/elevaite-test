"""
Database service layer using SQLModel

This module provides high-level database operations using SQLModel ORM.
It replaces the previous raw SQL implementation with proper ORM operations.
"""

import uuid as uuid_module
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Session, select, desc

from .database import engine
from .models import (
    Workflow,
    WorkflowExecution,
    StepType,
    ExecutionStatus,
)


class DatabaseService:
    """Database service providing high-level operations"""

    def __init__(self):
        self.engine = engine

    # Workflow operations
    async def save_workflow(
        self, workflow_id: str, workflow_data: Dict[str, Any]
    ) -> str:
        """Save or update a workflow"""
        with Session(self.engine) as session:
            # Check if workflow exists
            existing = session.exec(
                select(Workflow).where(
                    Workflow.workflow_id == uuid_module.UUID(workflow_id)
                )
            ).first()

            if existing:
                # Update existing workflow
                for key, value in workflow_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                session.add(existing)
            else:
                # Create new workflow
                workflow = Workflow(
                    workflow_id=uuid_module.UUID(workflow_id),
                    name=workflow_data.get("name", "Untitled Workflow"),
                    description=workflow_data.get("description"),
                    version=workflow_data.get("version", "1.0.0"),
                    execution_pattern=workflow_data.get(
                        "execution_pattern", "sequential"
                    ),
                    configuration=workflow_data,
                    global_config=workflow_data.get("global_config", {}),
                    tags=workflow_data.get("tags", []),
                    timeout_seconds=workflow_data.get("timeout_seconds"),
                    created_by=workflow_data.get("created_by"),
                )
                session.add(workflow)

            session.commit()
            return workflow_id

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow by ID"""
        with Session(self.engine) as session:
            workflow = session.exec(
                select(Workflow).where(
                    Workflow.workflow_id == uuid_module.UUID(workflow_id)
                )
            ).first()

            if workflow:
                return workflow.configuration
            return None

    async def list_workflows(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all workflows"""
        with Session(self.engine) as session:
            workflows = session.exec(
                select(Workflow)
                .offset(offset)
                .limit(limit)
                .order_by(desc(Workflow.created_at))
            ).all()

            return [
                {
                    "workflow_id": str(workflow.workflow_id),
                    "name": workflow.name,
                    "description": workflow.description,
                    "version": workflow.version,
                    "status": workflow.status,
                    "created_at": workflow.created_at.isoformat(),
                    "configuration": workflow.configuration,
                }
                for workflow in workflows
            ]

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        with Session(self.engine) as session:
            workflow = session.exec(
                select(Workflow).where(
                    Workflow.workflow_id == uuid_module.UUID(workflow_id)
                )
            ).first()

            if workflow:
                session.delete(workflow)
                session.commit()
                return True
            return False

    # Execution operations
    async def create_execution(self, execution_data: Dict[str, Any]) -> str:
        """Create a new workflow execution"""
        with Session(self.engine) as session:
            execution = WorkflowExecution(
                workflow_id=uuid_module.UUID(execution_data["workflow_id"]),
                user_id=execution_data.get("user_id"),
                session_id=execution_data.get("session_id"),
                organization_id=execution_data.get("organization_id"),
                status=ExecutionStatus.PENDING,
                input_data=execution_data.get("input_data", {}),
                execution_metadata=execution_data.get("metadata", {}),
                started_at=datetime.now(timezone.utc),
            )

            session.add(execution)
            session.commit()
            session.refresh(execution)

            return str(execution.execution_id)

    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get an execution by ID"""
        with Session(self.engine) as session:
            execution = session.exec(
                select(WorkflowExecution).where(
                    WorkflowExecution.execution_id == uuid_module.UUID(execution_id)
                )
            ).first()

            if execution:
                return {
                    "execution_id": str(execution.execution_id),
                    "workflow_id": str(execution.workflow_id),
                    "status": execution.status,
                    "user_id": execution.user_id,
                    "session_id": execution.session_id,
                    "organization_id": execution.organization_id,
                    "input_data": execution.input_data,
                    "output_data": execution.output_data,
                    "step_io_data": execution.step_io_data,
                    "metadata": execution.execution_metadata,
                    "error_message": execution.error_message,
                    "started_at": (
                        execution.started_at.isoformat()
                        if execution.started_at
                        else None
                    ),
                    "completed_at": (
                        execution.completed_at.isoformat()
                        if execution.completed_at
                        else None
                    ),
                    "execution_time_seconds": execution.execution_time_seconds,
                    "created_at": execution.created_at.isoformat(),
                }
            return None

    async def update_execution(
        self, execution_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update an execution"""
        with Session(self.engine) as session:
            execution = session.exec(
                select(WorkflowExecution).where(
                    WorkflowExecution.execution_id == uuid_module.UUID(execution_id)
                )
            ).first()

            if execution:
                for key, value in update_data.items():
                    if hasattr(execution, key):
                        setattr(execution, key, value)

                session.add(execution)
                session.commit()
                return True
            return False

    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List executions with optional filtering"""
        with Session(self.engine) as session:
            query = select(WorkflowExecution)

            if workflow_id:
                query = query.where(
                    WorkflowExecution.workflow_id == uuid_module.UUID(workflow_id)
                )
            if status:
                query = query.where(WorkflowExecution.status == status)

            executions = session.exec(
                query.offset(offset)
                .limit(limit)
                .order_by(desc(WorkflowExecution.created_at))
            ).all()

            return [
                {
                    "execution_id": str(execution.execution_id),
                    "workflow_id": str(execution.workflow_id),
                    "status": execution.status,
                    "user_id": execution.user_id,
                    "started_at": (
                        execution.started_at.isoformat()
                        if execution.started_at
                        else None
                    ),
                    "completed_at": (
                        execution.completed_at.isoformat()
                        if execution.completed_at
                        else None
                    ),
                    "execution_time_seconds": execution.execution_time_seconds,
                    "created_at": execution.created_at.isoformat(),
                }
                for execution in executions
            ]

    # Step type operations
    async def register_step_type(self, step_data: Dict[str, Any]) -> str:
        """Register a new step type"""
        with Session(self.engine) as session:
            # Check if step type already exists
            existing = session.exec(
                select(StepType).where(StepType.step_type == step_data["step_type"])
            ).first()

            if existing:
                # Update existing step type
                for key, value in step_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                session.add(existing)
                step_type_id = str(existing.step_type_id)
            else:
                # Create new step type
                step_type = StepType(
                    step_type=step_data["step_type"],
                    name=step_data["name"],
                    description=step_data.get("description"),
                    category=step_data.get("category", "utility"),
                    execution_type=step_data.get("execution_type", "local"),
                    function_reference=step_data["function_reference"],
                    parameters_schema=step_data.get("parameters_schema", {}),
                    response_schema=step_data.get("response_schema", {}),
                    endpoint_config=step_data.get("endpoint_config", {}),
                    tags=step_data.get("tags", []),
                    version=step_data.get("version", "1.0.0"),
                    author=step_data.get("author"),
                    documentation_url=step_data.get("documentation_url"),
                    example_config=step_data.get("example_config", {}),
                    registered_by=step_data.get("registered_by"),
                )
                session.add(step_type)
                session.commit()
                session.refresh(step_type)
                step_type_id = str(step_type.step_type_id)

            session.commit()
            return step_type_id

    async def get_step_type(self, step_type: str) -> Optional[Dict[str, Any]]:
        """Get a step type by name"""
        with Session(self.engine) as session:
            step = session.exec(
                select(StepType).where(StepType.step_type == step_type)
            ).first()

            if step:
                return {
                    "step_type": step.step_type,
                    "name": step.name,
                    "description": step.description,
                    "category": step.category,
                    "execution_type": step.execution_type,
                    "function_reference": step.function_reference,
                    "parameters_schema": step.parameters_schema,
                    "response_schema": step.response_schema,
                    "endpoint_config": step.endpoint_config,
                    "tags": step.tags,
                    "is_active": step.is_active,
                    "version": step.version,
                    "created_at": step.created_at.isoformat(),
                }
            return None

    async def list_step_types(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all step types"""
        with Session(self.engine) as session:
            query = select(StepType).where(StepType.is_active == True)

            if category:
                query = query.where(StepType.category == category)

            step_types = session.exec(query.order_by(StepType.name)).all()

            return [
                {
                    "step_type": step.step_type,
                    "name": step.name,
                    "description": step.description,
                    "category": step.category,
                    "execution_type": step.execution_type,
                    "tags": step.tags,
                    "version": step.version,
                    "created_at": step.created_at.isoformat(),
                }
                for step in step_types
            ]
