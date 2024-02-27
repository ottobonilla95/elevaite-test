from sqlalchemy.orm import Session

from elevaitedb.db import models
from elevaitedb.schemas import configuration as schema


def get_configuration_by_id(db: Session, application_id: int, instance_id: int):
    return (
        db.query(models.Configuration)
        .filter(models.Configuration.applicationId == application_id)
        .filter(models.Configuration.id == instance_id)
        .first()
    )


def create_configuration(
    db: Session,
    configurationCreate: schema.ConfigurationCreate,
):
    _configuration = models.Configuration(
        instanceId=configurationCreate.instanceId,
        applicationId=configurationCreate.applicationId,
        raw=configurationCreate.raw,
    )
    # app.applicationType = createApplicationDTO
    db.add(_configuration)
    db.commit()
    db.refresh(_configuration)
    return _configuration
