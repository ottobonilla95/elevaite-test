from typing import Optional
from pydantic import BaseModel, Field
from typing import List

class EventPayload(BaseModel):
    event_id: Optional[int]
    service_level_date: str
    category: str
    data_source: Optional[str]
    service_target: float
    actual_service_level: Optional[float]
    slo_breach_penalty: Optional[str]


class ConversationPayload(BaseModel):
    actor: str
    content: str

class InferencePayload(BaseModel):
    conversation_payload: List[ConversationPayload]
    query: str
    skip_llm_call: bool
    use_openai_directly: bool = Field(default=False)


