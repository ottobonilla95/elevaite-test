from typing import List, Union
from pydantic import BaseModel, UUID4
from qdrant_client.http.models import Distance


class CollectionBase(BaseModel):
    name: str
    size: int
    distance: Distance = Distance.COSINE


class CollectionCreate(CollectionBase):
    pass


class Collection(CollectionBase):
    id: UUID4
    projectId: UUID4

    class Config:
        orm_mode = True


class QdrantMetadata(BaseModel):
    document_title: str
    page_title: str
    source: str
    tokenSize: int


class QdrantPayload(BaseModel):
    metadata: QdrantMetadata
    page_content: str


class QdrantScroll(BaseModel):
    id: str
    payload: Union[QdrantPayload, None]
    vector: Union[List[float], None]
    shard_key: Union[str, None]


# class QdrantResponse(BaseModel):
#     __root__: Tuple[QdrantScroll, Union[str, None]]
