"""
Database service layer using SQLModel

This module provides high-level database operations using SQLModel ORM.
It replaces the previous raw SQL implementation with proper ORM operations.
"""

import uuid as uuid_module
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Session, select, desc

from .models import (
    Workflow,
    WorkflowExecution,
    StepType,
    ExecutionStatus,
)


class DatabaseService:
    """Database service providing high-level operations"""

    def __init__(self):
        # Stateless service; sessions are provided by callers
        pass

    # Workflow operations
    def save_workflow(
        self, session: Session, workflow_id: str, workflow_data: Dict[str, Any]
    ) -> str:
        """Save or update a workflow"""
        # Check if workflow exists
        existing = session.exec(
            select(Workflow).where(
                Workflow.workflow_id == uuid_module.UUID(workflow_id)
            )
        ).first()

        if existing:
            # Update only known fields explicitly
            existing.name = workflow_data.get("name", existing.name)
            existing.description = workflow_data.get(
                "description", existing.description
            )
            existing.version = workflow_data.get("version", existing.version)
            existing.execution_pattern = workflow_data.get(
                "execution_pattern", existing.execution_pattern
            )
            existing.configuration = workflow_data
            existing.global_config = workflow_data.get(
                "global_config", existing.global_config
            )
            existing.tags = workflow_data.get("tags", existing.tags)
            existing.timeout_seconds = workflow_data.get(
                "timeout_seconds", existing.timeout_seconds
            )
            existing.created_by = workflow_data.get("created_by", existing.created_by)
            session.add(existing)
        else:
            # Create new workflow
            workflow = Workflow(
                workflow_id=uuid_module.UUID(workflow_id),
                name=workflow_data.get("name", "Untitled Workflow"),
                description=workflow_data.get("description"),
                version=workflow_data.get("version", "1.0.0"),
                execution_pattern=workflow_data.get("execution_pattern", "sequential"),
                configuration=workflow_data,
                global_config=workflow_data.get("global_config", {}),
                tags=workflow_data.get("tags", []),
                timeout_seconds=workflow_data.get("timeout_seconds"),
                created_by=workflow_data.get("created_by"),
            )
            session.add(workflow)

        session.commit()
        return workflow_id

    def get_workflow(
        self, session: Session, workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a workflow by ID"""
        workflow = session.exec(
            select(Workflow).where(
                Workflow.workflow_id == uuid_module.UUID(workflow_id)
            )
        ).first()
        return workflow.configuration if workflow else None

    def list_workflows(
        self, session: Session, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all workflows"""
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

    def delete_workflow(self, session: Session, workflow_id: str) -> bool:
        """Delete a workflow"""
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
    def create_execution(self, session: Session, execution_data: Dict[str, Any]) -> str:
        """Create a new workflow execution"""
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

    def get_execution(
        self, session: Session, execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get an execution by ID"""
        execution = session.exec(
            select(WorkflowExecution).where(
                WorkflowExecution.execution_id == uuid_module.UUID(execution_id)
            )
        ).first()

        if not execution:
            return None

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
                execution.started_at.isoformat() if execution.started_at else None
            ),
            "completed_at": (
                execution.completed_at.isoformat() if execution.completed_at else None
            ),
            "execution_time_seconds": execution.execution_time_seconds,
            "created_at": execution.created_at.isoformat(),
        }

    def update_execution(
        self, session: Session, execution_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update an execution"""
        execution = session.exec(
            select(WorkflowExecution).where(
                WorkflowExecution.execution_id == uuid_module.UUID(execution_id)
            )
        ).first()

        if not execution:
            return False

        for key, value in update_data.items():
            if hasattr(execution, key):
                setattr(execution, key, value)

        session.add(execution)
        session.commit()
        return True

    def list_executions(
        self,
        session: Session,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List executions with optional filtering"""
        query = select(WorkflowExecution)

        if workflow_id:
            query = query.where(
                WorkflowExecution.workflow_id == uuid_module.UUID(workflow_id)
            )
        if status:
            status_enum = ExecutionStatus(status) if isinstance(status, str) else status
            if status_enum:
                query = query.where(WorkflowExecution.status == status_enum)

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
                    execution.started_at.isoformat() if execution.started_at else None
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
    def register_step_type(self, session: Session, step_data: Dict[str, Any]) -> str:
        """Register a new step type"""
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

    def get_step_type(
        self, session: Session, step_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get a step type by name"""
        step = session.exec(
            select(StepType).where(StepType.step_type == step_type)
        ).first()
        if not step:
            return None
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

    def list_step_types(
        self, session: Session, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all step types"""
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
