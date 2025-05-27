from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class DemoInitializationDetails(BaseModel):
    added_count: int
    skipped_count: int
    updated_count: Optional[int] = None
    added_prompts: Optional[List[str]] = None
    added_agents: Optional[List[str]] = None
    updated_agents: Optional[List[str]] = None


class DemoInitializationResponse(BaseModel):
    success: bool
    message: str
    details: Dict[str, Any]


class DemoStatusResponse(BaseModel):
    prompts_initialized: bool
    agents_initialized: bool
    total_prompts: int
    total_agents: int
    available_deployment_codes: Dict[str, str]
