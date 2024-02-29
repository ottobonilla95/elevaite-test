from sqlalchemy.orm import Session

from elevaitedb.db import models
from elevaitedb.schemas import instance as schema


def get_instances(db: Session, applicationId: int, skip: int = 0, limit: int = 0):
    return (
        db.query(models.Instance)
        .filter(models.Instance.applicationId == applicationId)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_instance_by_id(db: Session, applicationId: int, id: int):
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
        applicationId=createInstanceDTO.applicationId,
        selectedPipelineId=createInstanceDTO.selectedPipelineId,
        status=schema.InstanceStatus.STARTING,
        startTime=createInstanceDTO.startTime,
        datasetId=createInstanceDTO.datasetId,
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
        setattr(_ipss, var, value) if value else None

    db.add(_ipss)
    db.commit()
    db.refresh(_ipss)
    return _ipss
