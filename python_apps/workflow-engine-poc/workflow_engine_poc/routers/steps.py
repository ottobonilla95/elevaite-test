"""
Step registration and management endpoints
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any

from ..step_registry import StepRegistry
from ..util import api_key_or_user_guard
from ..schemas import StepConfigCreate, StepRegistrationResponse, RegisteredStepsResponse, StepInfoResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/steps", tags=["steps"])


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
        return StepRegistrationResponse(message="Step registered successfully", step_type=step_config.step_type)
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
        return RegisteredStepsResponse(steps=[StepInfoResponse(**step) for step in steps], total=len(steps))
    except Exception as e:
        logger.error(f"Failed to list steps: {e}")
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
            raise HTTPException(status_code=404, detail=f"Step type '{step_type}' not found")

        return StepInfoResponse(**step_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get step info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
