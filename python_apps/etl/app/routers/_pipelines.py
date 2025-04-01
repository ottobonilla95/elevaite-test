from fastapi import APIRouter
from typing import List, Dict, Any
from rbac_api import RBACValidatorProvider
from elevaitelib.pipelines.schemas.requests import (
    CreatePipelinesRequest,
    DeletePipelinesRequest,
    MonitorPipelinesRequest,
    RerunPipelinesRequest,
)
from elevaitelib.pipelines.service import (
    create_pipelines_for_provider,
    delete_pipelines_for_provider,
    monitor_pipelines_for_provider,
    rerun_pipelines_for_provider,
    get_available_providers,
)

rbacValidator = RBACValidatorProvider.get_instance()

router = APIRouter(prefix="/_pipeline", tags=["_pipelines"])


@router.get("/providers", response_model=List[str])
def get_providers():
    """
    Returns a list of all supported pipeline providers.
    """
    return get_available_providers()


@router.post("/create", response_model=Dict[str, Any])
def create_pipelines(payload: CreatePipelinesRequest):
    """
    Create pipelines for the given provider using provided file paths.
    """
    return create_pipelines_for_provider(payload.provider_type, payload.file_paths)


@router.delete("/delete", response_model=Dict[str, Any])
def delete_pipelines(payload: DeletePipelinesRequest):
    """
    Delete pipelines for the given provider using provided pipeline IDs.
    """
    return delete_pipelines_for_provider(payload.provider_type, payload.pipeline_ids)


@router.post("/monitor", response_model=Dict[str, Any])
def monitor_pipelines(payload: MonitorPipelinesRequest):
    """
    Monitor pipelines for the given provider using provided execution IDs.
    """
    return monitor_pipelines_for_provider(payload.provider_type, payload.execution_ids)


@router.post("/rerun", response_model=Dict[str, Any])
def rerun_pipelines(payload: RerunPipelinesRequest):
    """
    Rerun pipelines for the given provider using provided execution IDs.
    """
    return rerun_pipelines_for_provider(payload.provider_type, payload.execution_ids)
