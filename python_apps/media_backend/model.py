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
    duration_days: Optional[int] = Field(None, alias="duration(days)")
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
    full_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @classmethod
    def parse_obj(cls, obj):
        try:
            # Handle the 'full_data' field parsing
            if 'full_data' in obj and isinstance(obj['full_data'], str):
                try:
                    obj['full_data'] = json.loads(obj['full_data'])
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to decode 'full_data' as JSON: {e}. Input: {obj['full_data']}")

            # Normalize field names in 'full_data'
            if isinstance(obj.get('full_data'), dict):
                obj['full_data'] = {k.replace(' ', '_'): v for k, v in obj['full_data'].items()}
            
            return super().parse_obj(obj)
        
        except Exception as e:
            # Log or re-raise the error with context
            print(f"Error while parsing object: {e}. Input data: {obj}")
            # raise ValueError(f"Error while parsing object: {e}. Input data: {obj}")

    class Config:
        extra = "allow"
        populate_by_name = True
        str_strip_whitespace = True

class SearchResult(BaseModel):
    results: List[AdCreative]
    total: int
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

class IntentOutput(BaseModel):
    required_outcomes: List[int]
    unrelated_query: bool
    vector_search:bool
    parameters: Optional[Dict[str,str]]
    enhanced_query: Optional[str]
    follow_up:Optional[str]
class ExecutiveSummary(BaseModel):
    objectives: str
    target_audience: str
    budget: str
    campaign_duration: str
class TargetAudienceDemographic(BaseModel):
    age_range: str
    gender: str
    income_level: str
    interests: List[str]
    location: str
    behavioral_data: str
class MediaMixStrategy(BaseModel):
    channel_products: str
    tactics: str
    budget_allocation: str
    expected_reach: str
    justification: str
class CreativeStrategy(BaseModel):
    asset_type: str
    description: str
    purpose: str
    distribution_channels: List[str]
class MeasurementMetric(BaseModel):
    metric: str
    description: str
    target: str
    reporting_frequency: str
class MediaPlanOutput(BaseModel):
    executive_summary: ExecutiveSummary
    target_audience: TargetAudienceDemographic
    media_mix_strategy: List[MediaMixStrategy]
    creative_strategy: List[CreativeStrategy]
    measurement_and_evaluation: List[MeasurementMetric]
    message: str

# Analysis Prompt
class OverallTrend(BaseModel):
    analysis: str
    top_brands: List[str]

class InsightRecommendation(BaseModel):
    recommendation: str
    supporting_insight: str

class CampaignStrategy(BaseModel):
    objective: str
    insight_recommendation: InsightRecommendation

class ToneAndMood(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class CallToAction(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class SeasonHoliday(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class CampaignDuration(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class BookedImpressions(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class TargetingOptions(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class Conversion(BaseModel):
    insight_recommendation: InsightRecommendation

class CreativeInsights(BaseModel):
    key_trends: List[str]

class CreativeStrategy(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class CreativeContentType(BaseModel):
    description: str
    insight_recommendation: InsightRecommendation

class AnalysisOfTrends(BaseModel):
    overall_trends: OverallTrend
    campaign_strategy: CampaignStrategy
    tone_and_mood: ToneAndMood
    call_to_action: CallToAction
    season_holiday: SeasonHoliday
    campaign_duration: CampaignDuration
    booked_impressions: BookedImpressions
    targeting_options: TargetingOptions
    conversion: Optional[Conversion]
    creative_insights: CreativeInsights
    creative_strategy: CreativeStrategy
    creative_content_type: CreativeContentType

class AnalysisOfTrendsOne(BaseModel):
    overall_trends: OverallTrend
    campaign_strategy: CampaignStrategy
    tone_and_mood: ToneAndMood
    call_to_action: CallToAction
    season_holiday: SeasonHoliday
    campaign_duration: CampaignDuration

class AnalysisOfTrendsTwo(BaseModel):
    booked_impressions: BookedImpressions
    targeting_options: TargetingOptions
    conversion: Optional[Conversion]

class AnalysisOfTrendsThree(BaseModel):
    creative_insights: CreativeInsights
    creative_strategy: CreativeStrategy
    creative_content_type: CreativeContentType
    
# Campaign Performance Currently not using class.
class CampaignPerformance(BaseModel):
    brand: str
    product: str
    campaign_objective: str
    campaign_duration: str
    delivered_impressions: int
    actions_clicks: int
    value_to_money: float  # conversion rate in percentage
    creative_snapshot: str
class CampaignPerformanceReport(BaseModel):
    campaigns: List[CampaignPerformance]

# Creative Insights
class CreativeElements(BaseModel):
    creative_thumbnail: str
    brand_elements: str
    seasonal_holiday_elements: Optional[str]
    visual_elements: str
    color_tone: str
    cinematography: Optional[str]
    # audio_elements: str
    narrative_structure: Optional[str]

class CreativeInsight(BaseModel):
    brand: str
    product: str
    creative_snapshot: str
    creative_elements: CreativeElements

class CreativeInsightsReport(BaseModel):
    creatives: Optional[List[CreativeInsight]]
    # general_insights: Optional[str]


# Performance Summary
class PerformanceSummary(BaseModel):
    ad_objective: str
    call_to_action: str
    tone_and_mood: str
    duration_category: str
    unique_selling_proposition: str
    event_context: Optional[str]
    creative_performance: str
    overall_performance: str

class MediaPlanCreative(BaseModel):
    id: str
    file_name: str
    campaign_folder: str
    ad_objective: Optional[str] = None
    duration_days: Optional[int] = None
    duration_category: Optional[str] = None
    target_market: Optional[str] = None
    target_audience: Optional[str] = None
    tone_mood: Optional[str] = None
    weekends: Optional[int] = None
    holidays: Optional[str] = None
    national_events: Optional[str] = None
    sport_events: Optional[str] = None
    strategy: Optional[str] = None
    visual_elements: Optional[Dict[str, Any]] = None
    imagery: Optional[str] = None
    targeting: Optional[str] = None
    industry: Optional[str] = None
    conversion: Optional[float] = None
    booked_measure_impressions: Optional[float] = None
    delivered_measure_impressions: Optional[float] = None

class MediaPlanSearchResult(BaseModel):
    results: List[MediaPlanCreative]
    total: int

class MarkdownRequest(BaseModel):
    markdown: str


class MessageData(BaseModel):
    topic: Optional[str] = None
    message_query: str
    enhanced_query: str
    vector_data: List[dict] 
    creative_data: List[str] = []
    media_plan_output: str = ""
    creative_insights_output: str = ""
    campaign_performance_output: str = ""
    general_response_string: str = ""