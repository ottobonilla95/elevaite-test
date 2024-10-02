from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
    
class AdCreative(BaseModel):
    id: str
    file_name: str
    campaign_folder: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    type: Optional[str] = None
    booked_measure_impressions: Optional[float] = None
    delivered_measure_impressions: Optional[float] = None
    duration_days: Optional[int] = None
    duration_category: Optional[str] = None
    industry: Optional[str] = None
    brand: Optional[str] = None
    brand_type: Optional[str] = None
    season_holiday: Optional[str] = None
    product_service: Optional[str] = None
    ad_objective: Optional[str] = None
    targeting: Optional[str] = None
    tone_mood: Optional[str] = None
    clicks: Optional[int] = None
    conversion: Optional[float] = None
    creative_url: Optional[str] = None
    md5_hash: Optional[str] = None
    full_data: Optional[Dict[str, Any]] = Field(default=None)

    @classmethod
    def parse_obj(cls, obj):
        # Handle the 'full_data' field parsing
        if 'full_data' in obj and isinstance(obj['full_data'], str):
            try:
                obj['full_data'] = json.loads(obj['full_data'])
            except json.JSONDecodeError:
                obj['full_data'] = None
        return super().parse_obj(obj)

    class Config:
        extra = "allow"
        populate_by_name = True
        str_strip_whitespace = True

class SearchResult(BaseModel):
    results: List[AdCreative]
    total: int


# The Paylaods coming in
class ConversationPayload(BaseModel):
    actor: str
    content: str

class InferencePayload(BaseModel):
    conversation_payload: List[ConversationPayload]
    query: str
    skip_llm_call: bool