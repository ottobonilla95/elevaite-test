from datetime import datetime
import json
from pprint import pprint
from fastapi import HTTPException
from sqlalchemy.orm import Session

import pika

from app.util.name_generatior import get_random_name
from app.util.RedisSingleton import RedisSingleton
from app.util import func as util_func
from elevaitedb.schemas.application import Application, is_application
from elevaitedb.schemas.instance import (
    Instance,
    InstanceChartData,
    InstanceCreate,
    InstancePipelineStepStatus,
    InstancePipelineStepStatusUpdate,
    InstanceStatus,
    InstanceUpdate,
    is_instance,
)
from elevaitedb.schemas.pipeline import Pipeline, PipelineStepStatus, is_pipeline
from elevaitedb.schemas.configuration import (
    ConfigurationCreate,
    Configuration,
    PreProcessFormDTO,
    S3IngestFormDataDTO,
    is_configuration,
)
from elevaitedb.schemas.dataset import DatasetCreate, is_dataset
from elevaitedb.crud import (
    pipeline as pipeline_crud,
    application as application_crud,
    instance as instance_crud,
    configuration as configuration_crud,
    dataset as dataset_crud,
)


def getApplicationInstances(db: Session, application_id: int) -> list[Instance]:
    instances = instance_crud.get_instances(db, application_id, limit=100)
    return instances


def getApplicationInstanceById(
    db: Session, application_id: int, instance_id: str
) -> Instance:
    instances = instance_crud.get_instance_by_id(db, application_id, instance_id)
    return instances


def createApplicationInstance(
    db: Session,
    application_id: int,
    createInstanceDto: S3IngestFormDataDTO | PreProcessFormDTO,
    rmq: pika.BlockingConnection,
) -> Instance:

    # TODO: This will be changed with the pipeline rework
    app = application_crud.get_application_by_id(db, application_id)

    if not is_application(app):
        raise HTTPException(status_code=404, detail="Application not found")

    _pipeline = pipeline_crud.get_pipeline_by_id(
        db, createInstanceDto.selectedPipelineId
    )

    # _dataset = None

    if not createInstanceDto.datasetId:
        _dataset = dataset_crud.create_dataset(
            db,
            dataset_create=DatasetCreate(
                name=get_random_name(),
                projectId=createInstanceDto.projectId,
            ),
        )
    else:
        _dataset = dataset_crud.get_dataset_by_id(db, createInstanceDto.datasetId)

    createInstanceDto.datasetId = str(_dataset.id)

    _configuration_raw = json.dumps(
        createInstanceDto, default=lambda o: o.__dict__, sort_keys=True, indent=4
    )
    _configuration_create = ConfigurationCreate(
        applicationId=application_id,
        isTemplate=createInstanceDto.isTemplate,
        name=createInstanceDto.configurationName,
        raw=_configuration_raw,
    )

    _configuration = configuration_crud.create_configuration(db, _configuration_create)

    if not is_dataset(_dataset):
        raise HTTPException(status_code=404, detail="Application not found")

    _instance_create = InstanceCreate(
        applicationId=application_id,
        creator=createInstanceDto.creator,
        datasetId=_dataset.id,
        startTime=util_func.get_iso_datetime(),
        selectedPipelineId=createInstanceDto.selectedPipelineId,
        name=createInstanceDto.name,
        status=InstanceStatus.STARTING,
        configurationId=_configuration.id,
        configurationRaw=_configuration_raw,
        projectId=createInstanceDto.projectId,
    )

    _instance = instance_crud.create_instance(db, _instance_create)
    if not is_instance(_instance):
        raise HTTPException(
            status_code=500, detail="Error inserting instance in database"
        )

    if not is_pipeline(_pipeline):
        _instance_update = InstanceUpdate(
            comment="Pipeline was not found.", status=InstanceStatus.FAILED
        )
        res = instance_crud.update_instance(
            db, application_id, _instance.id, _instance_update
        )
        return res

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
        )
        _instance_pipeline_step = instance_crud.add_pipeline_step(
            db, _instance.id, _ipss
        )

    _data = {
        "id": str(_instance.id),
        "dto": createInstanceDto,
        "application_id": application_id,
    }

    def get_routing_key(application_id: int) -> str:
        match application_id:
            case 1:
                return "s3_ingest"
            case 2:
                return "preprocess"
            case _:
                return "default"

    rmq.channel().basic_publish(
        exchange="",
        body=json.dumps(_data, default=vars),
        routing_key=get_routing_key(application_id=application_id),
    )
    # # Maybe we should do this like this?
    #     return instance_crud.get_instance_by_id(
    #         db, applicationId=application_id, id=_instance.id
    #     )

    __instance = instance_crud.get_instance_by_id(
        db, applicationId=application_id, id=_instance.id
    )

    pprint(__instance.configuration.__dict__)

    return __instance


def approveApplicationInstance(
    db: Session, application_id: int, instance_id: str
) -> Instance:

    _end_time = util_func.get_iso_datetime()
    _instance = instance_crud.update_instance(
        db,
        application_id,
        instance_id,
        InstanceUpdate(status=InstanceStatus.COMPLETED, endTime=_end_time),
    )

    if not is_instance(_instance):
        raise HTTPException(500, "Error updating instance.")

    _pipeline = pipeline_crud.get_pipeline_by_id(db, _instance.selectedPipelineId)
    if not is_pipeline(_pipeline):
        raise HTTPException(500, "Selected Pipeline doesn't exist")

    _ipss = instance_crud.update_pipeline_step(
        db,
        instance_id,
        _pipeline.exit,
        InstancePipelineStepStatusUpdate(
            endTime=_end_time, status=PipelineStepStatus.COMPLETED
        ),
    )

    return getApplicationInstanceById(db, application_id, instance_id)


def getApplicationInstanceChart(
    application_id: int, instance_id: str
) -> InstanceChartData:
    r = RedisSingleton().connection

    if r.ping():
        res = r.json().get(instance_id)

        return InstanceChartData(
            avgSize=res["avg_size"],
            ingestedItems=res["ingested_items"],
            totalItems=res["total_items"],
            totalSize=res["total_size"],
            ingestedSize=res["ingested_size"],
            ingestedChunks=res["ingested_chunks"],
        )


def getApplicationInstanceConfiguration(
    db: Session, application_id: int, instance_id: str
) -> Configuration:
    res = configuration_crud.get_configuration_by_id(db, application_id, instance_id)
    if not is_configuration(res):
        raise HTTPException(404, "Configuration not found")

    return res
