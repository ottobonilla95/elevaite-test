from pydantic import BaseModel, UUID4

from .dataset import Dataset


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: UUID4
    datasets: list[Dataset]

    class Config:
        orm_mode = True
