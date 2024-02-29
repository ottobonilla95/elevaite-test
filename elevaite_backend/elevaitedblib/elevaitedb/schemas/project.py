from pydantic import BaseModel

from .dataset import Dataset


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str
    datasets: list[Dataset]

    class Config:
        orm_mode = True
