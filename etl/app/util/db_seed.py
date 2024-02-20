from sqlalchemy.orm import Session

from app.schemas.application import ApplicationCreate, ApplicationType
from app.crud.application import create_application


application1: ApplicationCreate = ApplicationCreate(
    title="S3 Connector",
    creator="elevAIte",
    applicationType=ApplicationType.INGEST,
    description="Ingest data from an S3 bucket",
    version="1.0",
    icon="",
)

application2: ApplicationCreate = ApplicationCreate(
    title="Preprocess Pipelines",
    creator="elevAIte",
    applicationType=ApplicationType.PREPROCESS,
    description="Preprocess ingested data",
    version="1.0",
    icon="",
)


def seed_db(db: Session):
    res1 = create_application(db, application1)
    res2 = create_application(db, application2)

    return [res1, res2]
