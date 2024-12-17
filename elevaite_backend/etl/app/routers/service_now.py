import json
import os
import re
from typing import Annotated, Any
import uuid
from dotenv import load_dotenv
from elevaitelib.schemas.configuration import (
    ConfigurationCreate,
    ServiceNowIngestDataDTO,
)
from elevaitelib.schemas.dataset import DatasetCreate
from elevaitelib.schemas.instance import (
    InstanceCreate,
    InstancePipelineStepStatus,
    InstanceStatus,
)
from elevaitelib.schemas.pipeline import PipelineStepStatus
from fastapi import APIRouter, Body, Depends, HTTPException, Request
import pika
from sqlalchemy.orm import Session

from elevaitelib.schemas import (
    service_now as schemas,
    #    api as api_schemas,
)

from app.util.service_now_seed import service_now_seed
from app.util.func import get_routing_key
from .deps import get_db, get_rabbitmq_connection
from elevaitelib.orm.crud import (
    pipeline as pipeline_crud,
    instance as instance_crud,
    configuration as configuration_crud,
    dataset as dataset_crud,
)
from elevaitelib.util import func as util_func

# from rbac_api import (
#    route_validator_map,
# )

router = APIRouter(prefix="/servicenow", tags=["servicenow"])


@router.post("/ingest")
def ingestServiceNowTickets(
    # request: Request, # uncomment when using validator
    dto: Annotated[schemas.ServiceNowIngestBody, Body()],
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'ingestServiceNowTickets')]), # uncomment this to use validator
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
):
    # db: Session = request.state.db # uncomment this when using validator
    load_dotenv()
    if not bool(re.match("^[a-z0-9][a-z0-9-]{2,62}$", dto.dataset_name)):
        raise HTTPException(400, "Dataset Name must match /^[a-z0-9][a-z0-9-]{2,62}$/")
    projectId = os.getenv("SERVICE_NOW_PROJECT")
    if projectId is None:
        raise Exception("ServiceNow Project ID has not been set in the environment")
    pipelineId = os.getenv("SERVICE_NOW_PIPELINE")
    if pipelineId is None:
        raise Exception("ServiceNow Pipeline ID has not been set in the environment")

    _existing_dataset = dataset_crud.get_dataset_by_name(db=db, name=dto.dataset_name)
    if _existing_dataset is not None:
        raise HTTPException(
            403,
            f"Dataset with name {dto.dataset_name} already exists. Dataset names must be unique.",
        )

    _dataset = dataset_crud.create_dataset(
        db=db,
        dataset_create=DatasetCreate(name=dto.dataset_name, projectId=uuid.UUID(projectId), description=""),
    )

    _pipeline = pipeline_crud.get_pipeline_by_id(db=db, pipeline_id=pipelineId, project_id=projectId, filter_function=None)
    if _pipeline is None:
        raise Exception("Pipeline not found")

    _conf_raw = ServiceNowIngestDataDTO(
        creator="ServiceNow",
        datasetId=str(_dataset.id),
        datasetName=dto.dataset_name,
        parent=None,
        projectId=projectId,
        selectedPipelineId=pipelineId,
        tickets=dto.tickets,
        version=None,
    )
    _conf_create = ConfigurationCreate(
        isTemplate=False,
        name=f"{dto.dataset_name}-conf",
        raw=_conf_raw.dict(),
        pipelineId=_pipeline.id,
        datasetId=_dataset.id,
    )
    _conf = configuration_crud.create_configuration(db=db, configurationCreate=_conf_create)

    _instance = instance_crud.create_instance(
        db=db,
        createInstanceDTO=InstanceCreate(
            comment=None,
            configurationId=_conf.id,
            configurationRaw=json.dumps(_conf_raw.json()),
            creator="ServiceNow",
            name=f"{dto.dataset_name}-instance",
            projectId=uuid.UUID(projectId),
            pipelineId=uuid.UUID(pipelineId),
            startTime=util_func.get_iso_datetime(),
            status=InstanceStatus.STARTING,
            endTime=None,
            executionId=None,
        ),
    )

    for ps in _pipeline.steps:
        _status = PipelineStepStatus.IDLE
        _start_time = None
        if ps.id == _pipeline.entry:
            _status = PipelineStepStatus.RUNNING
            _start_time = util_func.get_iso_datetime()
        _ipss = InstancePipelineStepStatus(
            stepId=ps.id,
            instanceId=_instance.id,
            status=_status,
            startTime=_start_time,
            endTime=None,
            meta=[],
        )
        _instance_pipeline_step = instance_crud.add_pipeline_step(db, str(_instance.id), _ipss)

    _data = {
        "id": str(_instance.id),
        "dto": _conf_raw,
        "configurationName": _conf.name,
        "application_id": 1,
    }

    rmq.channel().basic_publish(
        exchange="",
        body=json.dumps(_data, default=vars),
        routing_key=get_routing_key(application_id=1),
    )


@router.post("/seed")
def seedServiceNowPipeline(db: Session = Depends(get_db)):
    return service_now_seed(db)
