# from pprint import pprint
# from typing import Annotated
# from fastapi import APIRouter, Body, Depends
# from pydantic import BaseModel
# from sqlalchemy.orm import Session
# from ..services import projects as project_service
# from elevaitedb.schemas import (
#     project as project_schemas,
# )
# from .deps import get_db


# router = APIRouter(prefix="/project", tags=["projects"])


# @router.get("", response_model=list[project_schemas.Project])
# def getProjects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     return project_service.get_projects(db, skip, limit)


# @router.get("/{project_id}/", response_model=project_schemas.Project)
# def getProjectById(project_id: str, db: Session = Depends(get_db)):
#     return project_service.get_projecct_by_id(db=db, project_id=project_id)


# @router.post("", response_model=project_schemas.Project)
# def createProject(
#     dto: Annotated[project_schemas.ProjectCreate, Body()], db: Session = Depends(get_db)
# ):
#     return project_service.create_project(db=db, dto=dto)
