# from sqlalchemy.orm import Session

# from elevaitedb.crud import project as project_crud
# from elevaitedb.schemas import project as project_schemas
# from elevaitedb.db import models


# def get_projects(db: Session, skip: int = 0, limit: int = 100):
#     return project_crud.get_projects(db=db, skip=skip, limit=limit)


# def get_projecct_by_id(db: Session, project_id: str):
#     return project_crud.get_project_by_id(db=db, project_id=project_id)


# def create_project(db: Session, dto: project_schemas.ProjectCreate):
#     return project_crud.create_project(db=db, project_create=dto)
