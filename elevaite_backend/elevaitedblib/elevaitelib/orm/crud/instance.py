import json
from sqlalchemy.orm import Session, Query
from uuid import UUID
from ..db import models
from ...schemas import instance as schema
from typing import Type, Callable


def get_instances(
    db: Session,
    applicationId: int,
    # project_id: UUID, # uncomment this when using validator
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
    skip: int = 0,
    limit: int = 0,
):

    query = db.query(models.Instance)
    # if filter_function is not None: # uncomment this when using validator
    # query = filter_function(query)

    return (
        query.filter(models.Instance.applicationId == applicationId)
        # .filter(models.Instance.projectId == project_id) # uncomment this when using validator
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_instance_by_id(db: Session, applicationId: int, id: str):
    return (
        db.query(models.Instance)
        .filter(models.Instance.applicationId == applicationId)
        .filter(models.Instance.id == id)
        .first()
    )


def create_instance(
    db: Session,
    createInstanceDTO: schema.InstanceCreate,
):
    _instance = models.Instance(
        creator=createInstanceDTO.creator,
        name=createInstanceDTO.name,
        startTime=createInstanceDTO.startTime,
        status=schema.InstanceStatus.STARTING,
        datasetId=createInstanceDTO.datasetId,
        selectedPipelineId=createInstanceDTO.selectedPipelineId,
        applicationId=createInstanceDTO.applicationId,
        configurationId=createInstanceDTO.configurationId,
        projectId=createInstanceDTO.projectId,
        configurationRaw=createInstanceDTO.configurationRaw,
    )
    # app.applicationType = createApplicationDTO
    db.add(_instance)
    db.commit()
    db.refresh(_instance)

    _chartData = models.InstanceChartData()
    # _chartData.instanceId = _instance.id
    _instance.chartData = _chartData

    db.add(_instance)
    db.add(_chartData)
    db.commit()
    db.refresh(_instance)

    print(_instance)

    return _instance


def update_instance(
    db: Session,
    application_id: int,
    instance_id: str,
    updateInstanceDTO: schema.InstanceUpdate,
):
    _instance = get_instance_by_id(db, applicationId=application_id, id=instance_id)
    if _instance is None:
        return None

    for var, value in vars(updateInstanceDTO).items():
        setattr(_instance, var, value) if value else None

    db.add(_instance)
    db.commit()
    db.refresh(_instance)
    return _instance


def update_instance_chart_data(
    db: Session, instance_id: str, updateChartData: schema.InstanceChartData
):
    _chartData = (
        db.query(models.InstanceChartData)
        .filter(models.InstanceChartData.instanceId == instance_id)
        .first()
    )
    for var, value in vars(updateChartData).items():
        setattr(_chartData, var, value) if value else None

    db.add(_chartData)
    db.commit()
    db.refresh(_chartData)
    return _chartData


def add_pipeline_step(
    db: Session,
    instance_id: str,
    dto: schema.InstancePipelineStepStatus,
):
    _ipss = models.InstancePipelineStepStatus(
        instanceId=instance_id,
        stepId=dto.stepId,
        status=dto.status,
        startTime=dto.startTime,
        endTime=dto.endTime,
        meta=dto.meta,
    )
    db.add(_ipss)
    db.commit()
    db.refresh(_ipss)
    return _ipss


def get_pipeline_step_by_ids(db: Session, instance_id: str, step_id: str):
    return (
        db.query(models.InstancePipelineStepStatus)
        .filter(models.InstancePipelineStepStatus.instanceId == instance_id)
        .filter(models.InstancePipelineStepStatus.stepId == step_id)
        .first()
    )


def update_pipeline_step(
    db: Session,
    instance_id: str,
    step_id: str,
    dto: schema.InstancePipelineStepStatusUpdate,
):
    _ipss = get_pipeline_step_by_ids(db, instance_id, step_id)
    if _ipss is None:
        return None

    for var, value in vars(dto).items():
        if var == "meta" and value:
            setattr(_ipss, var, list(map(lambda v: json.loads(v.json()), value)))
        else:
            setattr(_ipss, var, value) if value else None

    db.add(_ipss)
    db.commit()
    db.refresh(_ipss)
    return _ipss
