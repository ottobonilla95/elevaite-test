"""
Step Type Endpoints

Provides API endpoints for managing and querying workflow step types.
Supports both in-memory (StepRegistry) and database-backed step types.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlmodel import Session
from pydantic import BaseModel

from db.database import get_db
from workflow_core_sdk.services.steps_service import StepsService
from workflow_core_sdk.db.models.step_registry import StepType, StepTypeCreate, StepTypeUpdate


router = APIRouter(prefix="/api/steps", tags=["steps"])


# Response schemas
class StepSchemaResponse(BaseModel):
    """Response schema for step type with OpenAI-compatible schemas"""

    step_type: str
    name: str
    description: str
    category: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class StepTypeResponse(BaseModel):
    """Response schema for step type details"""

    id: str
    step_type: str
    name: str
    description: str
    category: str
    execution_type: str
    function_reference: str
    parameters_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    is_active: bool
    version: str
    created_at: str


class SyncRegistryRequest(BaseModel):
    """Request to sync step types from registry to database"""

    update_existing: bool = False


class SyncRegistryResponse(BaseModel):
    """Response from registry sync operation"""

    success: bool
    message: str
    created: int
    updated: int
    skipped: int


# Endpoints


@router.get("/schemas", response_model=List[StepSchemaResponse])
def get_step_schemas(
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
):
    """
    Get all step types with their input/output schemas in OpenAI format.

    This endpoint is designed for frontend applications that need to:
    - Display available step types
    - Build UI for step configuration
    - Create mapping interfaces between step inputs/outputs

    The schemas follow OpenAI function calling format, making them
    compatible with existing tool/function UI components.

    Query Parameters:
    - category: Filter by step category (e.g., "data_processing", "ai_llm")
    - is_active: Filter by active status (default: true)

    Returns:
    - List of step schemas with input/output definitions
    """
    try:
        schemas = StepsService.list_step_schemas(db, category, is_active)
        return schemas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve step schemas: {str(e)}"
        )


@router.get("/types", response_model=List[StepTypeResponse])
def list_step_types(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    List all registered step types with full details.

    This endpoint provides complete step type information including
    execution configuration, function references, and metadata.

    Query Parameters:
    - category: Filter by step category
    - is_active: Filter by active status

    Returns:
    - List of step type details
    """
    try:
        step_types = StepsService.list_step_types(db, category, is_active)
        return [
            StepTypeResponse(
                id=str(step.id),
                step_type=step.step_type,
                name=step.name,
                description=step.description or "",
                category=step.category.value if hasattr(step.category, "value") else str(step.category),
                execution_type=step.execution_type.value if hasattr(step.execution_type, "value") else str(step.execution_type),
                function_reference=step.function_reference,
                parameters_schema=step.parameters_schema,
                response_schema=step.response_schema,
                is_active=step.is_active,
                version=step.version,
                created_at=step.created_at,
            )
            for step in step_types
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list step types: {str(e)}")


@router.get("/types/{step_type}", response_model=StepTypeResponse)
def get_step_type(step_type: str, db: Session = Depends(get_db)):
    """
    Get details for a specific step type.

    Path Parameters:
    - step_type: Step type identifier (e.g., "tool_execution")

    Returns:
    - Step type details
    """
    db_step = StepsService.get_step_type(db, step_type)
    if not db_step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step type '{step_type}' not found")

    return StepTypeResponse(
        id=str(db_step.id),
        step_type=db_step.step_type,
        name=db_step.name,
        description=db_step.description or "",
        category=db_step.category.value if hasattr(db_step.category, "value") else str(db_step.category),
        execution_type=db_step.execution_type.value
        if hasattr(db_step.execution_type, "value")
        else str(db_step.execution_type),
        function_reference=db_step.function_reference,
        parameters_schema=db_step.parameters_schema,
        response_schema=db_step.response_schema,
        is_active=db_step.is_active,
        version=db_step.version,
        created_at=db_step.created_at,
    )


@router.get("/schemas/{step_type}", response_model=StepSchemaResponse)
def get_step_schema(step_type: str, db: Session = Depends(get_db)):
    """
    Get input/output schemas for a specific step type in OpenAI format.

    Path Parameters:
    - step_type: Step type identifier

    Returns:
    - Step schemas in OpenAI function calling format
    """
    schema = StepsService.get_step_schemas(db, step_type)
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step type '{step_type}' not found")

    return schema


@router.post("/types", response_model=StepTypeResponse, status_code=status.HTTP_201_CREATED)
def create_step_type(step_data: StepTypeCreate, db: Session = Depends(get_db)):
    """
    Register a new step type.

    This endpoint allows remote registration of custom step types.
    The step type will be stored in the database and can be used
    in workflow definitions.

    Request Body:
    - step_type: Unique identifier for the step type
    - name: Human-readable name
    - description: Step description
    - category: Step category
    - execution_type: How the step is executed (local, rpc, api, grpc)
    - function_reference: Python function path or endpoint reference
    - parameters_schema: JSON schema for step parameters
    - response_schema: JSON schema for step output

    Returns:
    - Created step type details
    """
    try:
        # Check if step type already exists
        existing = StepsService.get_step_type(db, step_data.step_type)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Step type '{step_data.step_type}' already exists"
            )

        step_type = StepsService.create_step_type(db, step_data.model_dump())

        return StepTypeResponse(
            id=str(step_type.id),
            step_type=step_type.step_type,
            name=step_type.name,
            description=step_type.description or "",
            category=step_type.category.value if hasattr(step_type.category, "value") else str(step_type.category),
            execution_type=step_type.execution_type.value
            if hasattr(step_type.execution_type, "value")
            else str(step_type.execution_type),
            function_reference=step_type.function_reference,
            parameters_schema=step_type.parameters_schema,
            response_schema=step_type.response_schema,
            is_active=step_type.is_active,
            version=step_type.version,
            created_at=step_type.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create step type: {str(e)}")


@router.put("/types/{step_type}", response_model=StepTypeResponse)
def update_step_type(step_type: str, update_data: StepTypeUpdate, db: Session = Depends(get_db)):
    """
    Update a step type.

    Path Parameters:
    - step_type: Step type identifier

    Request Body:
    - Fields to update (all optional)

    Returns:
    - Updated step type details
    """
    updated = StepsService.update_step_type(db, step_type, update_data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step type '{step_type}' not found")

    return StepTypeResponse(
        id=str(updated.id),
        step_type=updated.step_type,
        name=updated.name,
        description=updated.description or "",
        category=updated.category.value if hasattr(updated.category, "value") else str(updated.category),
        execution_type=updated.execution_type.value
        if hasattr(updated.execution_type, "value")
        else str(updated.execution_type),
        function_reference=updated.function_reference,
        parameters_schema=updated.parameters_schema,
        response_schema=updated.response_schema,
        is_active=updated.is_active,
        version=updated.version,
        created_at=updated.created_at,
    )


@router.delete("/types/{step_type}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step_type(step_type: str, db: Session = Depends(get_db)):
    """
    Delete a step type (soft delete).

    Path Parameters:
    - step_type: Step type identifier

    Returns:
    - 204 No Content on success
    """
    deleted = StepsService.delete_step_type(db, step_type)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Step type '{step_type}' not found")


@router.post("/sync-registry", response_model=SyncRegistryResponse)
async def sync_from_registry(
    request: Request,
    sync_request: SyncRegistryRequest,
    db: Session = Depends(get_db),
):
    """
    Sync step types from the in-memory StepRegistry to the database.

    This endpoint allows persisting step types that were registered
    during application startup (via StepRegistry.register_builtin_steps())
    to the database for API access.

    This is useful for:
    - Making in-memory step types available via API
    - Backing up step type definitions
    - Enabling remote step type queries

    Request Body:
    - update_existing: Whether to update existing step types (default: false)

    Returns:
    - Sync operation results with counts
    """
    try:
        # Get step registry from app state
        if not hasattr(request.app.state, "step_registry"):
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Step registry not initialized")

        step_registry = request.app.state.step_registry

        # Get all registered steps from the registry
        registry_steps = await step_registry.get_registered_steps()

        # Sync to database
        result = StepsService.sync_from_registry(db, registry_steps, update_existing=sync_request.update_existing)

        return SyncRegistryResponse(
            success=True,
            message=f"Synced {result['created']} new step types, updated {result['updated']}, skipped {result['skipped']}",
            created=result["created"],
            updated=result["updated"],
            skipped=result["skipped"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync step types: {str(e)}")
