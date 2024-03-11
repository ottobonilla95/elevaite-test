from sqlalchemy.orm import Session

from ..db import models
from ..schemas import configuration as schema


def get_configuration_by_id(db: Session, application_id: int, instance_id: int):
    return (
        db.query(models.Configuration)
        .filter(models.Configuration.applicationId == application_id)
        .filter(models.Configuration.instanceId == instance_id)
        .first()
    )


def get_configurations_of_application(db: Session, application_id: int):
    return (
        db.query(models.Configuration)
        .filter(models.Configuration.applicationId == application_id)
        .all()
    )


def create_configuration(
    db: Session,
    configurationCreate: schema.ConfigurationCreate,
):
    _configuration = models.Configuration(
        applicationId=configurationCreate.applicationId,
        name=configurationCreate.name,
        isTemplate=configurationCreate.isTemplate,
        raw=configurationCreate.raw,
    )
    # app.applicationType = createApplicationDTO
    db.add(_configuration)
    db.commit()
    db.refresh(_configuration)
    return _configuration
