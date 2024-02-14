from enum import Enum
from pydantic import BaseModel


class ApplicationType(str, Enum):
    INGEST = "ingest"
    PREPROCESS = "preprocess"


class ApplicationBase(BaseModel):
    id: str
    title: str
    icon: str
    description: str
    version: str
    creator: str
    applicationType: ApplicationType
