from datetime import datetime
import json
from pprint import pprint
from typing import Any, List
from fastapi import HTTPException
from sqlalchemy.orm import Session

import pika
from uuid import UUID
from app.util.name_generator import get_random_name
from app.util.RedisSingleton import RedisSingleton
from app.util.ElasticSingleton import ElasticSingleton
from elevaitedb.util import func as util_func
from elevaitedb.schemas.application import Application, is_application
from elevaitedb.schemas.instance import (
    Instance,
    InstanceChartData,
    InstanceCreate,
    InstancePipelineStepStatus,
    InstancePipelineStepStatusUpdate,
    InstanceStatus,
    InstanceUpdate,
    InstanceCreateDTO,
    InstanceLogs,
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
from elevaitedb.schemas.collection import CollectionCreate
from elevaitedb.crud import (
    pipeline as pipeline_crud,
    application as application_crud,
    instance as instance_crud,
    configuration as configuration_crud,
    dataset as dataset_crud,
    collection as collection_crud,
)
from elevaitedb.db import models


def getApplicationInstances(
        db: Session, application_id: int,
        # project_id: UUID # uncomment this when using validator
    ) -> List[models.Instance]:
    instances = instance_crud.get_instances(
        db, 
        application_id,
        # project_id, # uncomment this when using validator
        limit=100
    )
    return instances


def getApplicationInstanceById(
    db: Session, application_id: int, instance_id: str
) -> models.Instance:
    _instance = instance_crud.get_instance_by_id(db, application_id, instance_id)
    if _instance is None:
        raise HTTPException(404, "Instance not found")
    return _instance


def createApplicationInstance(
    db: Session,
    application_id: int,
    createInstanceDto: InstanceCreateDTO,
    rmq: pika.BlockingConnection,
) -> models.Instance:

    # TODO: This will be changed with the pipeline rework
    app = application_crud.get_application_by_id(db, application_id)

    if not is_application(app):
        raise HTTPException(status_code=404, detail="Application not found")

    _configuration = configuration_crud.get_configuration_by_id(
        db, application_id=application_id, id=str(createInstanceDto.configurationId)
    )

    if _configuration is None:
        raise HTTPException(404, "Configuration not found")

    _raw_configuration = _configuration.raw
    if _raw_configuration["type"] == "ingest":
        _conf = S3IngestFormDataDTO(**_raw_configuration)
    elif _raw_configuration["type"] == "preprocess":
        _conf = PreProcessFormDTO(**_raw_configuration)
        if _conf.collectionId is None:
            _collection = collection_crud.create_collection(
                db=db,
                projectId=_conf.projectId,
                cc=CollectionCreate(name=get_random_name()),
            )
        else:
            _collection = collection_crud.get_collection_by_id(
                db=db, collectionId=_conf.collectionId
            )
        _conf.collectionId = str(_collection.id)
        _raw_configuration["collectionId"] = str(_collection.id)
    else:
        raise HTTPException(
            status_code=402, detail="Configuration Type must be ingest or preprocess"
        )

    _pipeline = pipeline_crud.get_pipeline_by_id(db, _conf.selectedPipelineId)

    # _dataset = None

    if not _conf.datasetId:
        datasetName = (
            _conf.datasetName if _conf.datasetName is not None else get_random_name()
        )
        _dataset = dataset_crud.create_dataset(
            db,
            dataset_create=DatasetCreate(
                name=datasetName,
                projectId=createInstanceDto.projectId,
            ),
        )
        tags = dataset_crud.get_dataset_tags(db=db)
        _source_tag = list(filter(lambda x: x.name == "Source", tags))
        if len(_source_tag) == 1:
            source_tag = _source_tag[0]
            dataset_crud.add_tag_to_dataset(
                db=db, dataset_id=str(_dataset.id), tag_id=str(source_tag.id)
            )

    else:
        _dataset = dataset_crud.get_dataset_by_id(db, _conf.datasetId)
        if not is_dataset(_dataset):
            raise HTTPException(status_code=404, detail="Dataset not found")

    _conf.datasetId = str(_dataset.id)
    _raw_configuration["datasetId"] = str(_dataset.id)

    _instance_create = InstanceCreate(
        applicationId=application_id,
        creator=createInstanceDto.creator,
        datasetId=_dataset.id,
        startTime=util_func.get_iso_datetime(),
        selectedPipelineId=_pipeline.id,
        name=createInstanceDto.instanceName,
        status=InstanceStatus.STARTING,
        configurationId=_configuration.id,
        configurationRaw=json.dumps(_raw_configuration),
        projectId=createInstanceDto.projectId,
        comment=None,
        endTime=None,
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
            db, application_id, str(_instance.id), _instance_update
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
            db, str(_instance.id), _ipss
        )

    _data = {
        "id": str(_instance.id),
        "dto": _raw_configuration,
        "configurationName": _configuration.name,
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
        db, applicationId=application_id, id=str(_instance.id)
    )

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

    _pipeline = pipeline_crud.get_pipeline_by_id(
        db=db, pipeline_id=str(_instance.selectedPipelineId)
    )
    if not is_pipeline(_pipeline):
        raise HTTPException(500, "Selected Pipeline doesn't exist")

    _ipss = instance_crud.update_pipeline_step(
        db=db,
        instance_id=instance_id,
        step_id=str(_pipeline.exit),
        dto=InstancePipelineStepStatusUpdate(
            endTime=_end_time, status=PipelineStepStatus.COMPLETED
        ),
    )

    return getApplicationInstanceById(db, application_id, instance_id)


def getApplicationInstanceChart(
    application_id: int, instance_id: str
) -> InstanceChartData:
    r = RedisSingleton().connection

    if not r.ping():
        raise HTTPException(503, "Redis unavailable")
    _res = r.json().get(instance_id)
    if _res is None:
        raise HTTPException(404, "Instance data not found")
    res = json.loads(json.dumps(_res))

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


def getApplicationInstanceLogs(instance_id: str, limit: int = 100, offset: int = 0):
    es = ElasticSingleton()
    result: list[InstanceLogs] = []
    _entries = es.getAllInIndexPaginated(
        index=instance_id, offset=offset, pagesize=limit
    )
    for entry in _entries:
        result.append(InstanceLogs(**entry["_source"]))
    return result
