from pprint import pprint
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from app.services import configurations as conf_service
from app.routers.deps import get_db
from elevaitedb.schemas import (
    configuration as configuration_schemas,
)

router = APIRouter(
    prefix="/application/{application_id}/configuration", tags=["configurations"]
)


@router.get("", response_model=list[configuration_schemas.Configuration])
def getApplicationConfigurations(application_id: int, db: Session = Depends(get_db)):
    return conf_service.getConfigurationsOfApplication(db, application_id)


@router.get("/{configuration_id}", response_model=configuration_schemas.Configuration)
def getApplicationConfigurations(
    application_id: int, configuration_id: str, db: Session = Depends(get_db)
):
    return conf_service.getConfigurationById(
        db, application_id, conf_id=configuration_id
    )
