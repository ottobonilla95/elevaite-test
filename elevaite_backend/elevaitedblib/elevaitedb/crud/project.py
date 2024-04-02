from sqlalchemy.orm import Session

from ..db import models

# from ..schemas.project import ProjectCreate


# def get_projects(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Project_V1).offset(skip).limit(limit).all()


# def get_project_by_id(db: Session, project_id: str):
#     return db.query(models.Project_V1).filter(models.Project_V1.id == project_id).first()


# def create_project(db: Session, project_create: ProjectCreate):
#     _project = models.Project_V1(name=project_create.name)
#     db.add(_project)
#     db.commit()
#     db.refresh(_project)
#     return _project


def get_project_name(db: Session, project_id: str):
    _project = db.query(models.Project).filter(models.Project.id == project_id).first()
    return _project.name
