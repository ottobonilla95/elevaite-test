import uuid
import json
from typing import List, Callable
import elasticsearch
from fastapi import HTTPException
import fastjsonschema
from flytekit.remote import FlyteRemote
from sqlalchemy.orm import Session, Query
import pika
from app.util.name_generator import get_random_name
from app.util.RedisSingleton import RedisSingleton
from app.util.ElasticSingleton import ElasticSingleton
from elevaitelib.util import func as util_func
from elevaitelib.schemas.instance import (
    InstanceChartData,
    InstanceCreate,
    InstanceStatus,
    InstanceUpdate,
    InstanceCreateDTO,
    InstanceLogs,
    chart_data_from_redis,
    is_instance,
)
from elevaitelib.schemas.pipeline import Pipeline, PipelineStepStatus, is_pipeline
from elevaitelib.schemas.configuration import (
    Configuration,
    is_configuration,
)
from elevaitelib.schemas.dataset import DatasetCreate, is_dataset
from elevaitelib.schemas.collection import CollectionCreate
from elevaitelib.orm.crud import (
    pipeline as pipeline_crud,
    instance as instance_crud,
    configuration as configuration_crud,
    dataset as dataset_crud,
    collection as collection_crud,
)
from elevaitelib.orm.db import models

from app.util.func import get_routing_key


def getInstancesOfPipeline(
    db: Session,
    pipeline_id: str,
    project_id: uuid.UUID,  # uncomment this when using validator
    filter_function: Callable[[Query], Query],  # uncomment this when using validator
) -> List[models.Instance]:
    instances = instance_crud.get_instances_of_pipeline(
        db=db,
        pipelineId=pipeline_id,
        project_id=project_id,  # uncomment this when using validator
        filter_function=filter_function,  # uncomment this when using validator
        limit=100,
    )
    return instances


def getInstanceById(db: Session, instance_id: str) -> models.Instance:
    _instance = instance_crud.get_instance_by_id(db=db, id=instance_id)
    if _instance is None:
        raise HTTPException(404, "Instance not found")
    return _instance


def createInstance(
    db: Session,
    createInstanceDto: InstanceCreateDTO,
    rmq: pika.BlockingConnection,
    remote: FlyteRemote,
) -> models.Instance:
    _configuration = configuration_crud.get_configuration_by_id(
        db, id=str(createInstanceDto.configurationId)
    )

    if _configuration is None:
        raise HTTPException(404, "Configuration not found")

    _pipeline = pipeline_crud.get_pipeline_by_id(
        db=db, pipeline_id=str(createInstanceDto.pipelineId), filter_function=None
    )

    if _pipeline is None or not is_pipeline(_pipeline):
        raise HTTPException(404, "Pipeline not found")

    input_schema = json.loads(_pipeline.input)
    validator = fastjsonschema.compile(input_schema)

    try:
        validator(_configuration.raw)  # type: ignore
    except fastjsonschema.JsonSchemaException as e:
        raise HTTPException(400, "Configuration raw data is invalid")

    # _dataset = None

    # if not _conf.datasetId:
    #     datasetName = (
    #         _conf.datasetName if _conf.datasetName is not None else get_random_name()
    #     )
    #     _dataset = dataset_crud.create_dataset(
    #         db,
    #         dataset_create=DatasetCreate(
    #             name=datasetName, projectId=createInstanceDto.projectId, description=""
    #         ),
    #     )
    #     tags = dataset_crud.get_dataset_tags(db=db)
    #     _source_tag = list(filter(lambda x: x.name == "Source", tags))
    #     if len(_source_tag) == 1:
    #         source_tag = _source_tag[0]
    #         dataset_crud.add_tag_to_dataset(
    #             db=db, dataset_id=str(_dataset.id), tag_id=str(source_tag.id)
    #         )

    # else:
    #     _dataset = dataset_crud.get_dataset_by_id(db, _conf.datasetId)
    #     if not is_dataset(_dataset):
    #         raise HTTPException(status_code=404, detail="Dataset not found")

    # _conf.datasetId = str(_dataset.id)
    # _raw_configuration["datasetId"] = str(_dataset.id)

    _instance_create = InstanceCreate(
        creator=createInstanceDto.creator,
        startTime=util_func.get_iso_datetime(),
        pipelineId=_pipeline.id,
        name=createInstanceDto.instanceName,
        status=InstanceStatus.STARTING,
        configurationId=_configuration.id,
        configurationRaw=_configuration.raw,
        projectId=createInstanceDto.projectId,
        comment=None,
        endTime=None,
        executionId=None,
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
            db=db, instance_id=str(_instance.id), updateInstanceDTO=_instance_update
        )
        return res

    # for ps in _pipeline.steps:
    #     _status = PipelineStepStatus.IDLE
    #     _start_time = None
    #     if ps.id == _pipeline.entry:
    #         _status = PipelineStepStatus.RUNNING
    #         _start_time = util_func.get_iso_datetime()
    #     _ipss = InstancePipelineStepStatus(
    #         stepId=ps.id,
    #         instanceId=_instance.id,
    #         status=_status,
    #         startTime=_start_time,
    #         endTime=None,
    #         meta=[],
    #     )
    #     _instance_pipeline_step = instance_crud.add_pipeline_step(
    #         db, str(_instance.id), _ipss
    #     )

    wf = remote.fetch_workflow(name=_pipeline.flyte_name)

    exec = remote.execute(wf, inputs=_configuration.raw)
    instance_crud.update_instance(
        db=db,
        instance_id=str(_instance.id),
        updateInstanceDTO=InstanceUpdate(executionId=exec.id),
    )

    __instance = instance_crud.get_instance_by_id(db, id=str(_instance.id))

    return __instance

    # def approveInstance(db: Session, instance_id: str) -> Instance:

    #     _end_time = util_func.get_iso_datetime()
    #     _instance = instance_crud.update_instance(
    #         db=db,
    #         instance_id=instance_id,
    #         updateInstanceDTO=InstanceUpdate(
    #             status=InstanceStatus.COMPLETED, endTime=_end_time
    #         ),
    #     )

    #     if not is_instance(_instance):
    #         raise HTTPException(500, "Error updating instance.")

    #     _pipeline = pipeline_crud.get_pipeline_by_id(
    #         db=db, pipeline_id=str(_instance.pipelineId)
    #     )
    #     if not is_pipeline(_pipeline):
    #         raise HTTPException(500, "Selected Pipeline doesn't exist")

    #     _ipss = instance_crud.update_pipeline_step(
    #         db=db,
    #         instance_id=instance_id,
    #         step_id=str(_pipeline.exit),
    #         dto=InstancePipelineStepStatusUpdate(
    #             endTime=_end_time, status=PipelineStepStatus.COMPLETED
    #         ),
    #     )

    # return getInstanceById(db=db, instance_id=instance_id)


def getInstanceChart(instance_id: str) -> InstanceChartData:
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
    res = configuration_crud.get_configuration_by_id(
        db=db, id=str(instance.configurationId)
    )
    if not is_configuration(res):
        raise HTTPException(404, "Configuration not found")

    return res


def getInstanceLogs(instance_id: str, limit: int = 100, offset: int = 0):
    es = ElasticSingleton()
    result: list[InstanceLogs] = []
    try:
        _entries = es.getAllInIndexPaginated(
            index=instance_id, offset=offset, pagesize=limit
        )
        for entry in _entries:
            result.append(InstanceLogs(**entry["_source"]))
    except elasticsearch.NotFoundError:
        print("logs not found")
    except Exception as e:
        print(f"{type(e)} occured: {e}")
    finally:
        return result
