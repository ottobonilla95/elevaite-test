"""
Step registration and management endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any
from rbac_sdk.fastapi_helpers import require_permission_async, resource_builders, principal_resolvers

from ..step_registry import StepRegistry

logger = logging.getLogger(__name__)

# RBAC header constants
HDR_PROJECT_ID = "X-elevAIte-ProjectId"
HDR_ACCOUNT_ID = "X-elevAIte-AccountId"
HDR_ORG_ID = "X-elevAIte-OrganizationId"

router = APIRouter(prefix="/steps", tags=["steps"])

# RBAC guards: view_project (list/get) and edit_project (register)
_guard_view_project = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)

_guard_edit_project = require_permission_async(
    action="edit_project",
    resource_builder=resource_builders.project_from_headers(
        project_header=HDR_PROJECT_ID,
        account_header=HDR_ACCOUNT_ID,
        org_header=HDR_ORG_ID,
    ),
    principal_resolver=principal_resolvers.api_key_or_user(),
)


@router.post("/register")
async def register_step(
    step_config: Dict[str, Any],
    request: Request,
    _principal: str = Depends(_guard_edit_project),
):
    """
    Register a new step function.

    This enables RPC-like step registration where clients can
    register custom step functions that can be called during workflow execution.
    """
    try:
        step_registry: StepRegistry = request.app.state.step_registry
        await step_registry.register_step(step_config)
        return {"message": "Step registered successfully", "step_type": step_config.get("step_type")}
    except Exception as e:
        logger.error(f"Failed to register step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_registered_steps(
    request: Request,
    _principal: str = Depends(_guard_view_project),
):
    """List all registered step functions"""
    try:
        step_registry: StepRegistry = request.app.state.step_registry
        steps = await step_registry.get_registered_steps()
        return {"steps": steps, "total": len(steps)}
    except Exception as e:
        logger.error(f"Failed to list steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{step_type}")
async def get_step_info(
    step_type: str,
    request: Request,
    _principal: str = Depends(_guard_view_project),
):
    """Get information about a specific step type"""
    try:
        step_registry: StepRegistry = request.app.state.step_registry
        step_info = await step_registry.get_step_info(step_type)

        if not step_info:
            raise HTTPException(status_code=404, detail=f"Step type '{step_type}' not found")

        return step_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get step info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
