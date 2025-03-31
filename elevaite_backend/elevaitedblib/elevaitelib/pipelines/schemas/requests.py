from typing import List
from pydantic import BaseModel


class CreatePipelinesRequest(BaseModel):
    provider_type: str
    file_paths: List[str]


class DeletePipelinesRequest(BaseModel):
    provider_type: str
    pipeline_ids: List[str]


class MonitorPipelinesRequest(BaseModel):
    provider_type: str
    execution_ids: List[str]


class RerunPipelinesRequest(BaseModel):
    provider_type: str
    execution_ids: List[str]
