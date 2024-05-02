import json
import os
from typing import Annotated
import uuid
from dotenv import load_dotenv
from elevaitedb.schemas.configuration import (
    ConfigurationCreate,
    ServiceNowIngestDataDTO,
)
from elevaitedb.schemas.dataset import DatasetCreate
from elevaitedb.schemas.instance import InstanceCreate, InstanceStatus
from fastapi import APIRouter, Body, Depends
import pika
from rbac_api.utils.deps import get_db
from sqlalchemy.orm import Session
from elevaitedb.schemas import service_now as schemas

from app.util.service_now_seed import service_now_seed
from app.util.func import get_routing_key
from .deps import get_rabbitmq_connection
from elevaitedb.crud import (
    pipeline as pipeline_crud,
    application as application_crud,
    instance as instance_crud,
    configuration as configuration_crud,
    dataset as dataset_crud,
    collection as collection_crud,
)
from elevaitedb.util import func as util_func


router = APIRouter(prefix="/servicenow", tags=["servicenow"])


@router.post("/ingest")
def ingestServiceNowTickets(
    dto: Annotated[schemas.ServiceNowIngestBody, Body()],
    db: Session = Depends(get_db),
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
):
    load_dotenv()
    projectId = os.getenv("SERVICE_NOW_PROJECT")
    if projectId is None:
        raise Exception("ServiceNow Project ID has not been set in the environment")
    pipelineId = os.getenv("SERVICE_NOW_PIPELINE")
    if pipelineId is None:
        raise Exception("ServiceNow Pipeline ID has not been set in the environment")

    _dataset = dataset_crud.create_dataset(
        db=db,
        dataset_create=DatasetCreate(
            name=dto.dataset_name, projectId=uuid.UUID(projectId), description=""
        ),
    )

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
        applicationId=1,
        isTemplate=False,
        name=f"{dto.dataset_name}-conf",
        raw=_conf_raw,
    )
    _conf = configuration_crud.create_configuration(
        db=db, configurationCreate=_conf_create
    )

    _instance = instance_crud.create_instance(
        db=db,
        createInstanceDTO=InstanceCreate(
            applicationId=1,
            comment=None,
            configurationId=_conf.id,
            configurationRaw=json.dumps(_conf_raw.json()),
            creator="ServiceNow",
            datasetId=_dataset.id,
            name=f"{dto.dataset_name}-instance",
            projectId=uuid.UUID(projectId),
            selectedPipelineId=uuid.UUID(pipelineId),
            startTime=util_func.get_iso_datetime(),
            status=InstanceStatus.STARTING,
            endTime=None,
        ),
    )

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
