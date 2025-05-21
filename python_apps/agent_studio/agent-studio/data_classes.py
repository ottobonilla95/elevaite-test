import uuid
import pydantic
from typing import Optional, Dict, List
from datetime import datetime


class PromptReadListRequest(pydantic.BaseModel):
    app_name: str
    prompt_label: str


class PromptReadDeployedRequest(pydantic.BaseModel):
    app_name: str
    prompt_label: str


class PromptReadRequest(pydantic.BaseModel):
    app_name: str
    pid: uuid.UUID


class PromptObjectRequest(pydantic.BaseModel):
    """
    pid: randomUUID(),
    app_name: appName,
    vendor: selectedVendor,
    model_name: selectedModelName,
    prompt_label: selectedPromptLabel,
    prompt: selectedPrompt,
    hash: hash,
    temperature: temperature,
    max_tokens: maxTokens,
    version: version,
    is_deployed: false,
    deployed_time: new Date().toISOString(),
    """

    pid: uuid.UUID
    is_system_prompt: Optional[bool]
    app_name: str
    vendor: str
    ai_model_name: str
    prompt_label: str
    prompt: str
    hash: str
    temperature: str
    max_tokens: str
    version: Optional[str]
    tags: Optional[List[str]]
    is_deployed: Optional[bool]
    hyper_parameters: Optional[Dict[str, str]]
    variables: Optional[List[str]]
    deployed_time: Optional[datetime]


class PromptDeployRequest(pydantic.BaseModel):
    """
    pid: randomUUID(),
    app_name: appName,
    """

    pid: uuid.UUID
    app_name: str


class PromptObject(pydantic.BaseModel):
    pid: uuid.UUID
    prompt_label: str
    prompt: str
    sha_hash: str
    uniqueLabel: str
    appName: str
    version: str
    createdTime: datetime
    deployedTime: Optional[datetime]
    last_deployed: Optional[datetime]
    modelProvider: str
    modelName: str
    isDeployed: bool
    tags: Optional[List[str]]
    hyper_parameters: Optional[Dict[str, str]]
    variables: Optional[Dict[str, str]]
