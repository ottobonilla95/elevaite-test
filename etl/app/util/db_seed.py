from sqlalchemy.orm import Session

from elevaitedb.schemas.application import ApplicationCreate, ApplicationType
from elevaitedb.crud.application import create_application
from elevaitedb.schemas.pipeline import Pipeline, PipelineCreate
from elevaitedb.db import models
from .mockData import applications_list


application1: ApplicationCreate = ApplicationCreate(
    title="S3 Connector",
    creator="elevAIte",
    applicationType=ApplicationType.INGEST,
    description="Ingest data from an S3 bucket",
    version="1.0",
    icon="",
)

# pipeline1: PipelineCreate = PipelineCreate()

application2: ApplicationCreate = ApplicationCreate(
    title="Preprocess Pipelines",
    creator="elevAIte",
    applicationType=ApplicationType.PREPROCESS,
    description="Preprocess ingested data",
    version="1.0",
    icon="",
)


def seed_db(db: Session):
    # res1 = create_application(db, application1)
    # res2 = create_application(db, application2)

    res = []

    for app in applications_list:
        _app = (
            db.query(models.Application).filter(models.Application.id == app.id).first()
        )

        if _app:
            db.delete(_app)

        db.add(app)
        db.commit()
        db.refresh(app)
        res.append(app)

    # return [res1, res2]
    return res
