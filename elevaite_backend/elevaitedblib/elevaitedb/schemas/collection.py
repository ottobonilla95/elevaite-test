from pydantic import BaseModel, UUID4


class CollectionBase(BaseModel):
    name: str


class CollectionCreate(CollectionBase):
    pass


class Collection(CollectionBase):
    id: UUID4
    projectId: UUID4

    class Config:
        orm_mode = True
