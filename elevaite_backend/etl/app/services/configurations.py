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


def getConfigurationsOfApplication(db: Session, application_id: int):
    _conf = configuration_crud.get_configurations_of_application(db, application_id)
    return _conf


def getConfigurationById(db: Session, application_id: int, conf_id: str):
    _conf = configuration_crud.get_configuration_by_id(db, application_id, conf_id)
    return _conf


def createConfiguration(db: Session, create_configuration: ConfigurationCreate):
    _conf = configuration_crud.create_configuration(db, create_configuration)
    return _conf
