import json
from sqlalchemy.orm import Session

from ..db import models
from ..schemas import configuration as schema


def get_configuration_by_id(db: Session, application_id: int, id: str):
    return (
        db.query(models.Configuration)
        .filter(models.Configuration.applicationId == application_id)
        .filter(models.Configuration.id == id)
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
        raw=json.loads(
            json.dumps(
                configurationCreate.raw,
                default=lambda o: o.__dict__,
                sort_keys=True,
                indent=4,
            )
        ),
    )
    # app.applicationType = createApplicationDTO
    db.add(_configuration)
    db.commit()
    db.refresh(_configuration)
    return _configuration
