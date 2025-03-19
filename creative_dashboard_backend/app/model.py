from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class HealthCheckResponse(BaseModel):
    status: str

class ErrorResponse(BaseModel):
    error: str

class AdSurfaceBrandPair(BaseModel):
    Ad_Surface: str
    Brand: str

class AdSurfaceBrandPairsResponse(BaseModel):
    adsurface_brand_pairs: List[AdSurfaceBrandPair]

class CampaignDataResponse(BaseModel):
    campaigns: List[str]
    creative_data: List[Dict[str, Any]]
    campaign_data: List[Dict[str, Any]]

class ReloadResponse(BaseModel):
    status: str

class ConversationPayload(BaseModel):
    actor: str
    content: str

class InferencePayload(BaseModel):
    conversation_payload: List[ConversationPayload]
    query: str
    skip_llm_call: bool
    creative: Optional[str] = None 
    session_id: str
    user_id: str
    # selected_brand: Optional[str] = None
    # selected_ad_surface: Optional[str] = None
    # selected_campaign: Optional[str] = None

class InferenceResponse(BaseModel):
    response: str