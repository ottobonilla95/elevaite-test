import json
from typing import List
import elasticsearch
from elevaitelib.pipelines.service import create_pipelines_for_provider
from fastapi import HTTPException
from sqlalchemy.orm import Session, Query
from app.util.RedisSingleton import RedisSingleton
from app.util.ElasticSingleton import ElasticSingleton
from elevaitelib.util import func as util_func
from elevaitelib.schemas.application import is_application
from elevaitelib.schemas.instance import (
    Instance,
    InstanceChartData,
    InstanceCreate,
    InstancePipelineStepStatus,
    InstancePipelineStepStatusUpdate,
    InstanceStatus,
    InstanceUpdate,
    InstanceCreateDTO,
    InstanceLogs,
    chart_data_from_redis,
    is_instance,
)
from elevaitelib.schemas.pipeline import is_pipeline
from elevaitelib.schemas.configuration import (
    Configuration,
    PreProcessFormDTO,
    S3IngestFormDataDTO,
    is_configuration,
)
from elevaitelib.orm.crud import (
    pipeline as pipeline_crud,
    application as application_crud,
    instance as instance_crud,
    configuration as configuration_crud,
)
from elevaitelib.orm.db import models


def getApplicationInstances(
    db: Session,
    application_id: int,
    # project_id: uuid.UUID, # uncomment this when using validator
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
) -> List[models.Instance]:
    instances = instance_crud.get_instances(
        db,
        application_id,
        # project_id, # uncomment this when using validator
        # filter_function=filter_function, # uncomment this when using validator
        limit=100,
    )
    return instances


def getApplicationInstanceById(db: Session, application_id: int, instance_id: str) -> models.Instance:
    _instance = instance_crud.get_instance_by_id(db, application_id, instance_id)
    if _instance is None:
        raise HTTPException(404, "Instance not found")
    return _instance


def createApplicationInstance(
    db: Session,
    application_id: int,
    createInstanceDto: InstanceCreateDTO,
) -> models.Instance:
    _configuration = configuration_crud.get_configuration_by_id(db, id=str(createInstanceDto.configurationId))

    if _configuration is None:
        raise HTTPException(404, "Configuration not found")

    _pipeline = pipeline_crud.get_pipeline_by_id(db=db, pipeline_id=str(createInstanceDto.pipelineId), filter_function=None)

    if _pipeline is None or not is_pipeline(_pipeline):
        raise HTTPException(404, "Pipeline not found")

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
        raise HTTPException(status_code=500, detail="Error inserting instance in database")
        raise HTTPException(status_code=500, detail="Error inserting instance in database")

    if not is_pipeline(_pipeline):
        _instance_update = InstanceUpdate(comment="Pipeline was not found.", status=InstanceStatus.FAILED)
        res = instance_crud.update_instance(db=db, instance_id=str(_instance.id), updateInstanceDTO=_instance_update)
        return res

    create_pipelines_for_provider(createInstanceDto.provider, [_pipeline.model_dump()])

    instance_crud.update_instance(
        db=db,
        instance_id=str(_instance.id),
        updateInstanceDTO=InstanceUpdate(executionId="<EXECUTION ID>"),
    )

    __instance = instance_crud.get_instance_by_id(db, applicationId=application_id, id=str(_instance.id))

    return __instance


def approveApplicationInstance(db: Session, application_id: int, instance_id: str) -> Instance:
    _end_time = util_func.get_iso_datetime()
    _instance = instance_crud.update_instance(
        db,
        application_id,
        instance_id,
        InstanceUpdate(status=InstanceStatus.COMPLETED, endTime=_end_time),
    )

    if not is_instance(_instance):
        raise HTTPException(500, "Error updating instance.")

    _pipeline = pipeline_crud.get_pipeline_by_id(db=db, pipeline_id=str(_instance.selectedPipelineId))
    if not is_pipeline(_pipeline):
        raise HTTPException(500, "Selected Pipeline doesn't exist")

    _ipss = instance_crud.update_pipeline_step(
        db=db,
        instance_id=instance_id,
        step_id=str(_pipeline.exit),
        dto=InstancePipelineStepStatusUpdate(endTime=_end_time, status=PipelineStepStatus.COMPLETED),
    )

    return getApplicationInstanceById(db, application_id, instance_id)


def getApplicationInstanceChart(application_id: int, instance_id: str) -> InstanceChartData:
    r = RedisSingleton().connection

    if not r.ping():
        raise HTTPException(503, "Redis unavailable")
    _res = r.json().get(instance_id)
    if _res is None:
        raise HTTPException(404, "Instance data not found")
    res = json.loads(json.dumps(_res))

    return chart_data_from_redis(input=res)


def getInstanceConfiguration(db: Session, instance_id: str) -> Configuration:
    instance = instance_crud.get_instance_by_id(db=db, id=instance_id)
    if not is_instance(instance):
        raise HTTPException(404, "Instance not found")
    res = configuration_crud.get_configuration_by_id(db=db, id=str(instance.configurationId))
    if not is_configuration(res):
        raise HTTPException(404, "Configuration not found")

    return res


def getApplicationInstanceLogs(instance_id: str, limit: int = 100, offset: int = 0):
    es = ElasticSingleton()
    result: list[InstanceLogs] = []
    try:
        _entries = es.getAllInIndexPaginated(index=instance_id, offset=offset, pagesize=limit)
        _entries = es.getAllInIndexPaginated(index=instance_id, offset=offset, pagesize=limit)
        for entry in _entries:
            result.append(InstanceLogs(**entry["_source"]))
    except elasticsearch.NotFoundError:
        print("logs not found")
    except Exception as e:
        print(f"{type(e)} occured: {e}")
    finally:
        return result
