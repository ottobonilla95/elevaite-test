from pydantic import BaseModel


class BaseApplicationDTO(BaseModel):
    id: str
    title: str
    icon: str
    description: str
    version: str
    creator: str
