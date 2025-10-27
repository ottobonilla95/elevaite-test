"""
Policy Management API

Provides endpoints for dynamically managing OPA authorization policies.
Only accessible to superusers.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging

from app.services.policy_service import get_policy_service, PolicyService
from app.core.deps import get_current_superuser
from app.db.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================


class ServicePolicyCreate(BaseModel):
    """Schema for generating a service policy"""

    service_name: str = Field(
        ..., description="Name of the service (e.g., 'workflow_engine')"
    )
    resource_type: str = Field(..., description="Type of resource (e.g., 'workflow')")
    actions: Dict[str, List[str]] = Field(
        ..., description="Mapping of role to list of allowed actions"
    )
    belongs_to: str = Field(
        default="project",
        description="What the resource belongs to (organization, account, or project)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "workflow_engine",
                "resource_type": "workflow",
                "belongs_to": "project",
                "actions": {
                    "superadmin": [
                        "create_workflow",
                        "edit_workflow",
                        "view_workflow",
                        "delete_workflow",
                        "execute_workflow",
                    ],
                    "admin": [
                        "create_workflow",
                        "edit_workflow",
                        "view_workflow",
                        "delete_workflow",
                        "execute_workflow",
                    ],
                    "editor": [
                        "create_workflow",
                        "edit_workflow",
                        "view_workflow",
                        "execute_workflow",
                    ],
                    "viewer": ["view_workflow"],
                },
            }
        }


class PolicyUpload(BaseModel):
    """Schema for uploading a custom policy"""

    module_name: str = Field(
        ..., description="Name of the policy module (e.g., 'rbac/custom')"
    )
    rego_code: str = Field(..., description="The rego policy code")

    class Config:
        json_schema_extra = {
            "example": {
                "module_name": "rbac/custom_rules",
                "rego_code": 'package rbac\n\nimport rego.v1\n\nrole_check(assignment) if {\n  assignment.role == "analyst"\n  input.action == "export_data"\n}',
            }
        }


class PolicyResponse(BaseModel):
    """Schema for policy response"""

    module_name: str
    rego_code: str


class PolicyListItem(BaseModel):
    """Schema for policy list item"""

    id: str
    name: str


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str
    module_name: Optional[str] = None
    rego_code: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/policies/generate", response_model=MessageResponse, tags=["policies"])
async def generate_service_policy(
    data: ServicePolicyCreate,
    current_user: User = Depends(get_current_superuser),
    policy_service: PolicyService = Depends(get_policy_service),
):
    """
    Generate and upload a policy for a service.

    This endpoint generates a rego policy based on the provided service configuration
    and uploads it to OPA. The policy will define which roles can perform which actions
    on the specified resource type.

    **Only superusers can manage policies.**

    Example:
    ```json
    {
      "service_name": "workflow_engine",
      "resource_type": "workflow",
      "belongs_to": "project",
      "actions": {
        "admin": ["create_workflow", "edit_workflow", "view_workflow", "delete_workflow"],
        "editor": ["create_workflow", "edit_workflow", "view_workflow"],
        "viewer": ["view_workflow"]
      }
    }
    ```
    """
    logger.info(
        f"User {current_user.id} generating policy for service: {data.service_name}"
    )

    # Generate rego code
    rego_code = await policy_service.generate_service_policy(
        service_name=data.service_name,
        resource_type=data.resource_type,
        actions=data.actions,
        belongs_to=data.belongs_to,
    )

    # Validate syntax
    is_valid, error_msg = await policy_service.validate_rego_syntax(rego_code)
    if not is_valid:
        logger.error(f"Generated policy has syntax error: {error_msg}")
        raise HTTPException(
            status_code=400, detail=f"Generated policy has syntax error: {error_msg}"
        )

    # Upload to OPA
    module_name = f"rbac/{data.service_name}"
    success = await policy_service.upload_policy(module_name, rego_code)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload policy to OPA")

    logger.info(f"Successfully created policy: {module_name}")

    return MessageResponse(
        message=f"Policy for {data.service_name} created successfully",
        module_name=module_name,
        rego_code=rego_code,
    )


@router.post("/policies/upload", response_model=MessageResponse, tags=["policies"])
async def upload_custom_policy(
    data: PolicyUpload,
    current_user: User = Depends(get_current_superuser),
    policy_service: PolicyService = Depends(get_policy_service),
):
    """
    Upload a custom rego policy.

    This endpoint allows uploading custom rego code directly to OPA.
    Use this for advanced policy customization that can't be generated
    automatically.

    **Only superusers can manage policies.**

    The rego code will be validated before uploading.
    """
    logger.info(f"User {current_user.id} uploading custom policy: {data.module_name}")

    # Validate syntax
    is_valid, error_msg = await policy_service.validate_rego_syntax(data.rego_code)
    if not is_valid:
        logger.error(f"Policy has syntax error: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Invalid rego syntax: {error_msg}")

    # Upload to OPA
    success = await policy_service.upload_policy(data.module_name, data.rego_code)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload policy to OPA")

    logger.info(f"Successfully uploaded policy: {data.module_name}")

    return MessageResponse(message=f"Policy {data.module_name} uploaded successfully")


@router.get("/policies", response_model=List[PolicyListItem], tags=["policies"])
async def list_policies(
    current_user=Depends(get_current_superuser),
    policy_service: PolicyService = Depends(get_policy_service),
):
    """
    List all policy modules in OPA.

    Returns a list of all policy modules currently loaded in OPA.

    **Only superusers can view policies.**
    """
    logger.info(f"User {current_user.id} listing policies")

    policies = await policy_service.list_policies()
    return policies


@router.get(
    "/policies/{module_name:path}", response_model=PolicyResponse, tags=["policies"]
)
async def get_policy(
    module_name: str,
    current_user: User = Depends(get_current_superuser),
    policy_service: PolicyService = Depends(get_policy_service),
):
    """
    Get a specific policy module.

    Returns the rego code for the specified policy module.

    **Only superusers can view policies.**

    Example: `/policies/rbac/workflows` or `/policies/rbac/core`
    """
    logger.info(f"User {current_user.id} getting policy: {module_name}")

    rego_code = await policy_service.get_policy(module_name)

    if rego_code is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    return PolicyResponse(module_name=module_name, rego_code=rego_code)


@router.delete(
    "/policies/{module_name:path}", response_model=MessageResponse, tags=["policies"]
)
async def delete_policy(
    module_name: str,
    current_user: User = Depends(get_current_superuser),
    policy_service: PolicyService = Depends(get_policy_service),
):
    """
    Delete a policy module.

    Removes the specified policy module from OPA.

    **Only superusers can delete policies.**

    ⚠️ **Warning:** Deleting a policy may break authorization for services
    that depend on it. Use with caution!
    """
    logger.info(f"User {current_user.id} deleting policy: {module_name}")

    success = await policy_service.delete_policy(module_name)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete policy")

    logger.info(f"Successfully deleted policy: {module_name}")

    return MessageResponse(message=f"Policy {module_name} deleted successfully")
