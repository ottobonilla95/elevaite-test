from typing import TypeGuard
from pydantic import UUID4, BaseModel, Json


class ConfigurationBase(BaseModel):
    instanceId: UUID4
    applicationId: int
    raw: Json


class ConfigurationCreate(ConfigurationBase):
    pass


class Configuration(ConfigurationBase):
    id: str

    class Config:
        orm_mode = True


def is_configuration(var: object) -> TypeGuard[Configuration]:
    return var is not None and var.id
