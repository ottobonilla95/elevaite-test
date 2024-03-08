from sqlalchemy.orm import Session

from ..db import models
from ..schemas.project import ProjectCreate


def get_project_by_id(db: Session, project_id: str):
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def create_project(db: Session, project_create: ProjectCreate):
    _project = models.Project(name=project_create.name)
    db.add(_project)
    db.commit()
    db.refresh(_project)
    return _project
