
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

class PromptBase(BaseModel):
    prompt_label: str
    prompt: str
    unique_label: str
    app_name: str
    version: str
    ai_model_provider: str
    ai_model_name: str
    tags: Optional[List[str]] = None
    hyper_parameters: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None

class PromptCreate(PromptBase):
    sha_hash: Optional[str] = None

class PromptUpdate(BaseModel):
    prompt_label: Optional[str] = None
    prompt: Optional[str] = None
    unique_label: Optional[str] = None
    app_name: Optional[str] = None
    version: Optional[str] = None
    ai_model_provider: Optional[str] = None
    ai_model_name: Optional[str] = None
    is_deployed: Optional[bool] = None
    tags: Optional[List[str]] = None
    hyper_parameters: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None

class PromptInDB(PromptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pid: uuid.UUID
    sha_hash: str
    is_deployed: bool
    created_time: datetime
    deployed_time: Optional[datetime] = None
    last_deployed: Optional[datetime] = None

class PromptResponse(PromptInDB):
    pass

class PromptVersionBase(BaseModel):
    prompt_id: uuid.UUID
    version_number: str
    prompt_content: str
    commit_message: Optional[str] = None
    hyper_parameters: Optional[Dict[str, str]] = None
    created_by: Optional[str] = None

class PromptVersionCreate(PromptVersionBase):
    pass

class PromptVersionInDB(PromptVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

class PromptVersionResponse(PromptVersionInDB):
    pass

class PromptDeploymentBase(BaseModel):
    prompt_id: uuid.UUID
    environment: str
    version_number: str
    deployed_by: Optional[str] = None

class PromptDeploymentCreate(PromptDeploymentBase):
    pass

class PromptDeploymentInDB(PromptDeploymentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deployed_at: datetime
    is_active: bool

class PromptDeploymentResponse(PromptDeploymentInDB):
    pass

class PromptDeployRequest(BaseModel):
    pid: uuid.UUID
    app_name: str
    environment: str = "production"

class PromptReadRequest(BaseModel):
    app_name: str
    pid: uuid.UUID

class PromptReadListRequest(BaseModel):
    app_name: str
    prompt_label: str
