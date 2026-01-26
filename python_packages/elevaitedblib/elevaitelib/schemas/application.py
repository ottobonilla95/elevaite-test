from enum import Enum
from typing import Any, Dict, TypeGuard
from pydantic import BaseModel


class ApplicationType(str, Enum):
    INGEST = "ingest"
    PREPROCESS = "preprocess"


class ApplicationBase(BaseModel):
    title: str
    icon: str
    description: str
    version: str
    creator: str
    applicationType: ApplicationType


class ApplicationCreate(ApplicationBase):
    pass


class Application(ApplicationBase):
    id: int

    class Config:
        orm_mode = True


def is_application(val: Dict[str, Any] | None) -> TypeGuard[Application]:
    return (
        val is not None
        and isinstance(val, "object")
        and "applicationType" in val.keys()
    )
