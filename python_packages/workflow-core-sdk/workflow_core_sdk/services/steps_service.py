"""
Steps Service

Provides CRUD operations for step type management in the workflow system.
Supports both in-memory (StepRegistry) and database-backed step types.
"""

from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
import uuid

from ..db.models.step_registry import StepType, StepTypeCreate
from ..utils.schema_utils import (
    create_step_input_schema,
    create_step_output_schema,
)


class StepsService:
    """Service for managing workflow step types"""

    @staticmethod
    def list_step_types(
        session: Session,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[StepType]:
        """
        List all registered step types from the database.

        Args:
            session: Database session
            category: Filter by category
            is_active: Filter by active status

        Returns:
            List of step types
        """
        query = select(StepType)

        if category:
            query = query.where(StepType.category == category)
        if is_active is not None:
            query = query.where(StepType.is_active == is_active)

        return list(session.exec(query).all())

    @staticmethod
    def get_step_type(session: Session, step_type: str) -> Optional[StepType]:
        """
        Get a step type by its type identifier.

        Args:
            session: Database session
            step_type: Step type identifier (e.g., "tool_execution")

        Returns:
            StepType if found, None otherwise
        """
        query = select(StepType).where(StepType.step_type == step_type)
        return session.exec(query).first()

    @staticmethod
    def get_step_type_by_id(session: Session, step_id: str) -> Optional[StepType]:
        """
        Get a step type by its UUID.

        Args:
            session: Database session
            step_id: Step type UUID

        Returns:
            StepType if found, None otherwise
        """
        query = select(StepType).where(StepType.id == uuid.UUID(step_id))
        return session.exec(query).first()

    @staticmethod
    def create_step_type(session: Session, step_data: Dict[str, Any]) -> StepType:
        """
        Register a new step type in the database.

        Args:
            session: Database session
            step_data: Step type configuration

        Returns:
            Created StepType

        Example:
            >>> step_data = {
            ...     "step_type": "custom_processor",
            ...     "name": "Custom Processor",
            ...     "description": "Processes data in a custom way",
            ...     "category": "data_processing",
            ...     "execution_type": "local",
            ...     "function_reference": "my_module.custom_processor_step",
            ...     "parameters_schema": {...},
            ...     "response_schema": {...}
            ... }
            >>> step_type = StepsService.create_step_type(session, step_data)
        """
        # Validate required fields
        required_fields = ["step_type", "name", "function_reference", "execution_type"]
        for field in required_fields:
            if field not in step_data:
                raise ValueError(f"Missing required field: {field}")

        # Create step type
        step_type_create = StepTypeCreate(**step_data)
        step_type = StepType(**step_type_create.model_dump())

        session.add(step_type)
        session.commit()
        session.refresh(step_type)

        return step_type

    @staticmethod
    def update_step_type(
        session: Session, step_type: str, update_data: Dict[str, Any]
    ) -> Optional[StepType]:
        """
        Update a step type.

        Args:
            session: Database session
            step_type: Step type identifier
            update_data: Fields to update

        Returns:
            Updated StepType if found, None otherwise
        """
        db_step = StepsService.get_step_type(session, step_type)
        if not db_step:
            return None

        # Update fields
        for key, value in update_data.items():
            if hasattr(db_step, key) and value is not None:
                setattr(db_step, key, value)

        session.add(db_step)
        session.commit()
        session.refresh(db_step)

        return db_step

    @staticmethod
    def delete_step_type(session: Session, step_type: str) -> bool:
        """
        Delete a step type (soft delete by setting is_active=False).

        Args:
            session: Database session
            step_type: Step type identifier

        Returns:
            True if deleted, False if not found
        """
        db_step = StepsService.get_step_type(session, step_type)
        if not db_step:
            return False

        db_step.is_active = False
        session.add(db_step)
        session.commit()

        return True

    @staticmethod
    def get_step_schemas(session: Session, step_type: str) -> Optional[Dict[str, Any]]:
        """
        Get input and output schemas for a step type in OpenAI format.

        Args:
            session: Database session
            step_type: Step type identifier

        Returns:
            Dictionary with input_schema and output_schema in OpenAI format
        """
        db_step = StepsService.get_step_type(session, step_type)
        if not db_step:
            return None

        return {
            "step_type": db_step.step_type,
            "name": db_step.name,
            "description": db_step.description,
            "category": db_step.category,
            "input_schema": create_step_input_schema(
                step_type=db_step.step_type,
                parameters_schema=db_step.parameters_schema,
                description=f"Input parameters for {db_step.name}",
            ),
            "output_schema": create_step_output_schema(
                step_type=db_step.step_type,
                output_schema=db_step.response_schema
                or {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "result": {"description": "Step output"},
                    },
                },
                description=f"Output from {db_step.name}",
            ),
        }

    @staticmethod
    def list_step_schemas(
        session: Session,
        category: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> List[Dict[str, Any]]:
        """
        List all step types with their schemas in OpenAI format.

        This is useful for frontend applications that need to build
        UI components for step configuration and mapping.

        Args:
            session: Database session
            category: Filter by category
            is_active: Filter by active status

        Returns:
            List of step schemas in OpenAI format
        """
        step_types = StepsService.list_step_types(session, category, is_active)

        schemas = []
        for step_type in step_types:
            schema = StepsService.get_step_schemas(session, step_type.step_type)
            if schema:
                schemas.append(schema)

        return schemas

    @staticmethod
    def sync_from_registry(
        session: Session,
        registry_steps: List[Dict[str, Any]],
        update_existing: bool = False,
    ) -> Dict[str, int]:
        """
        Sync step types from a StepRegistry to the database.

        This allows step types registered in-memory (e.g., during startup)
        to be persisted to the database for API access.

        Args:
            session: Database session
            registry_steps: List of step configurations from StepRegistry
            update_existing: Whether to update existing step types

        Returns:
            Dictionary with counts: {"created": N, "updated": M, "skipped": K}
        """
        created = 0
        updated = 0
        skipped = 0

        for step_config in registry_steps:
            step_type = step_config.get("step_type")
            if not step_type:
                skipped += 1
                continue

            existing = StepsService.get_step_type(session, step_type)

            if existing:
                if update_existing:
                    StepsService.update_step_type(session, step_type, step_config)
                    updated += 1
                else:
                    skipped += 1
            else:
                StepsService.create_step_type(session, step_config)
                created += 1

        return {"created": created, "updated": updated, "skipped": skipped}
