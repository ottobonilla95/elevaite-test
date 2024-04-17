from datetime import datetime
from typing import Any, TypeGuard
from pydantic import UUID4, BaseModel


class DatasetVersionBase(BaseModel):
    commitId: str
    version: int


class DatasetVersionCreate(DatasetVersionBase):
    pass


class DatasetVersion(DatasetVersionBase):
    id: UUID4
    createDate: datetime

    class Config:
        orm_mode = True


class DatasetTagBase(BaseModel):
    name: str


class DatasetTagCreate(DatasetTagBase):
    pass


class DatasetTag(DatasetTagBase):
    id: UUID4

    class Config:
        orm_mode = True


class DatasetBase(BaseModel):
    name: str
    projectId: UUID4


class DatasetCreate(DatasetBase):
    pass


class Dataset(DatasetBase):
    id: UUID4
    versions: list[DatasetVersion]
    tags: list[DatasetTag]
    createDate: datetime
    updateDate: datetime | None

    class Config:
        orm_mode = True


def is_dataset(var: Any) -> TypeGuard[Dataset]:
    return var is not None and var["projectId"] is not None
