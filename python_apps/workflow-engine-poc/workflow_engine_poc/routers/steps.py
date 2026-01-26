"""
Step registration and management endpoints
"""

import logging
from typing import Literal
from fastapi import APIRouter, Request, HTTPException, Depends

from workflow_core_sdk import StepRegistry
from workflow_core_sdk.utils.variable_injection import get_builtin_variables
from ..util import api_key_or_user_guard
from ..schemas import (
    StepConfigCreate,
    StepRegistrationResponse,
    RegisteredStepsResponse,
    StepInfoResponse,
    BuiltinVariableInfo,
    BuiltinVariablesResponse,
)

SourceType = Literal["builtin", "context"]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/steps", tags=["steps"])

# Metadata for builtin variables (descriptions, examples, categories)
BUILTIN_VARIABLE_METADATA = {
    # Time-related (UTC)
    "current_time": {
        "description": "Current ISO timestamp in UTC",
        "example": "2026-01-19T15:30:45+00:00",
        "category": "time",
        "source": "builtin",
    },
    "current_time_utc": {
        "description": "Current ISO timestamp in UTC (explicit)",
        "example": "2026-01-19T15:30:45+00:00",
        "category": "time",
        "source": "builtin",
    },
    "current_date": {
        "description": "Current date in UTC (YYYY-MM-DD)",
        "example": "2026-01-19",
        "category": "time",
        "source": "builtin",
    },
    "current_date_utc": {
        "description": "Current date in UTC (explicit, YYYY-MM-DD)",
        "example": "2026-01-19",
        "category": "time",
        "source": "builtin",
    },
    "current_timestamp": {
        "description": "Current Unix timestamp (seconds since epoch)",
        "example": "1737297045",
        "category": "time",
        "source": "builtin",
    },
    "current_year": {
        "description": "Current year",
        "example": "2026",
        "category": "time",
        "source": "builtin",
    },
    "current_month": {
        "description": "Current month (1-12)",
        "example": "1",
        "category": "time",
        "source": "builtin",
    },
    "current_day": {
        "description": "Current day of month (1-31)",
        "example": "19",
        "category": "time",
        "source": "builtin",
    },
    "current_hour": {
        "description": "Current hour in UTC (0-23)",
        "example": "15",
        "category": "time",
        "source": "builtin",
    },
    "current_minute": {
        "description": "Current minute (0-59)",
        "example": "30",
        "category": "time",
        "source": "builtin",
    },
    # Time-related (local)
    "current_time_local": {
        "description": "Current ISO timestamp in server local timezone",
        "example": "2026-01-19T10:30:45-05:00",
        "category": "time",
        "source": "builtin",
    },
    "current_date_local": {
        "description": "Current date in server local timezone (YYYY-MM-DD)",
        "example": "2026-01-19",
        "category": "time",
        "source": "builtin",
    },
    # Unique identifiers
    "uuid": {
        "description": "Generates a new random UUID",
        "example": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "category": "identifier",
        "source": "builtin",
    },
    "execution_id": {
        "description": "Current workflow execution ID (from context, or generates UUID if not available)",
        "example": "exec-a1b2c3d4-e5f6-7890",
        "category": "context",
        "source": "context",
    },
    # Context variables (from execution context)
    "workflow_id": {
        "description": "Current workflow ID from execution context",
        "example": "wf-a1b2c3d4-e5f6-7890",
        "category": "context",
        "source": "context",
    },
    "user_id": {
        "description": "User ID from execution context",
        "example": "user-a1b2c3d4-e5f6-7890",
        "category": "context",
        "source": "context",
    },
    "user_name": {
        "description": "User display name from execution context",
        "example": "John Doe",
        "category": "context",
        "source": "context",
    },
    "session_id": {
        "description": "Session ID from execution context",
        "example": "sess-a1b2c3d4-e5f6-7890",
        "category": "context",
        "source": "context",
    },
}


@router.post("/register", response_model=StepRegistrationResponse)
async def register_step(
    step_config: StepConfigCreate,
    request: Request,
    _principal: str = Depends(api_key_or_user_guard("register_step")),
):
    """
    Register a new step function.

    This enables RPC-like step registration where clients can
    register custom step functions that can be called during workflow execution.
    """
    try:
        step_registry: StepRegistry = request.app.state.step_registry
        await step_registry.register_step(step_config.model_dump())
        return StepRegistrationResponse(
            message="Step registered successfully", step_type=step_config.step_type
        )
    except Exception as e:
        logger.error(f"Failed to register step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=RegisteredStepsResponse)
async def list_registered_steps(
    request: Request,
    _principal: str = Depends(api_key_or_user_guard("view_step")),
):
    """List all registered step functions"""
    try:
        step_registry: StepRegistry = request.app.state.step_registry
        steps = await step_registry.get_registered_steps()
        return RegisteredStepsResponse(
            steps=[StepInfoResponse(**step) for step in steps], total=len(steps)
        )
    except Exception as e:
        logger.error(f"Failed to list steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variables/builtin", response_model=BuiltinVariablesResponse)
async def list_builtin_variables(
    _principal: str = Depends(api_key_or_user_guard("view_step")),
):
    """
    List all available builtin variables for prompt templates.

    These variables can be used in prompt templates and input mappings
    using the {{variable_name}} syntax. They are automatically replaced
    with their values at runtime.

    Variables are sourced from:
    - **builtin**: Auto-generated values (timestamps, UUIDs)
    - **context**: Values from the execution context (user_id, workflow_id, etc.)
    """
    try:
        # Get the list of builtin variables from the SDK
        builtin_vars = get_builtin_variables()

        # Build response with metadata
        variables = []
        for var_name in builtin_vars.keys():
            metadata = BUILTIN_VARIABLE_METADATA.get(var_name, {})
            source_value: SourceType = metadata.get("source", "builtin")  # type: ignore[assignment]
            variables.append(
                BuiltinVariableInfo(
                    name=var_name,
                    description=metadata.get("description", f"Variable: {var_name}"),
                    example=metadata.get("example"),
                    category=metadata.get("category", "other"),
                    source=source_value,
                )
            )

        # Add context-only variables (not in get_builtin_variables but available from context)
        context_only_vars = ["workflow_id", "user_id", "user_name", "session_id"]
        for var_name in context_only_vars:
            if var_name not in builtin_vars:
                metadata = BUILTIN_VARIABLE_METADATA.get(var_name, {})
                variables.append(
                    BuiltinVariableInfo(
                        name=var_name,
                        description=metadata.get(
                            "description", f"Variable: {var_name}"
                        ),
                        example=metadata.get("example"),
                        category=metadata.get("category", "context"),
                        source="context",
                    )
                )

        # Sort by category then name for consistent ordering
        variables.sort(key=lambda v: (v.category, v.name))

        return BuiltinVariablesResponse(variables=variables, total=len(variables))
    except Exception as e:
        logger.error(f"Failed to list builtin variables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{step_type}", response_model=StepInfoResponse)
async def get_step_info(
    step_type: str,
    request: Request,
    _principal: str = Depends(api_key_or_user_guard("view_step")),
):
    """Get information about a specific step type"""
    try:
        step_registry: StepRegistry = request.app.state.step_registry
        step_info = await step_registry.get_step_info(step_type)

        if not step_info:
            raise HTTPException(
                status_code=404, detail=f"Step type '{step_type}' not found"
            )

        return StepInfoResponse(**step_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get step info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
