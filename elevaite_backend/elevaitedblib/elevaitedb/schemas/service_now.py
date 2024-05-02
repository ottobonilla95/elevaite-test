from typing import List
from pydantic import BaseModel


class ServiceNowTicket(BaseModel):
    problem_description: str
    source_ref_id: str
    source_url: str
    resolution: str


class ServiceNowIngestBody(BaseModel):
    dataset_name: str
    tickets: List[ServiceNowTicket]
