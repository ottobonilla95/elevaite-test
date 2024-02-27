from typing import TypeGuard
from pydantic import BaseModel


class DatasetBase(BaseModel):
    name: str
    projectId: str


class DatasetCreate(DatasetBase):
    pass


class Dataset(DatasetBase):
    id: str

    class Config:
        orm_mode = True


def is_dataset(var: object) -> TypeGuard[Dataset]:
    return var is not None and var.projectId is not None
