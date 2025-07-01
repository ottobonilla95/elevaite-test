from dataclasses import dataclass
from typing import Dict, List, Optional, Literal, Any

from db.schemas import AgentFunction, AgentFunctionInner

@dataclass
class DefaultPrompt:
    prompt_label: str
    prompt: str
    unique_label: str
    app_name: str
    version: str
    ai_model_provider: str
    ai_model_name: str
    tags: List[str]
    hyper_parameters: Dict[str, str]
    variables: Dict[str, str]

@dataclass
class DefaultAgent:
    name: str
    agent_type: Optional[Literal["router", "web_search", "data", "troubleshooting", "api", "weather", "toshiba"]]
    description: Optional[str]
    prompt_label: str
    persona: str
    functions: List[AgentFunction]
    routing_options: Dict[str, str]
    short_term_memory: bool
    long_term_memory: bool
    reasoning: bool
    input_type: List[Literal["text", "voice", "image"]]
    output_type: List[Literal["text", "voice", "image"]]
    response_type: Literal["json", "yaml", "markdown", "HTML", "None"]
    max_retries: int
    timeout: Optional[int]
    deployed: bool
    status: Literal["active", "paused", "terminated"]
    priority: Optional[int]
    failure_strategies: List[str]
    collaboration_mode: Literal["single", "team", "parallel", "sequential"]

AGENT_CODES = {
    "WebAgent": "w",
    "DataAgent": "d",
    "APIAgent": "a",
    "CommandAgent": "r",
    "HelloWorldAgent": "h",
    "ToshibaAgent": "t",
    "Intent Router": "ir",
    "Campaign Performance Agent": "cpa",
    "Qdrant Search Agent": "qsa",
    "Performance Summary Agent": "psa",
    "Media Planning Agent": "mpa",
    "Generic Response Agent": "gra",
}

DEFAULT_PROMPTS: List[DefaultPrompt] = [
    DefaultPrompt(
        prompt_label="Web Agent Prompt",
        prompt="You are a web agent that can search the web for information.",
        unique_label="WebAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["web", "search"],
        hyper_parameters={"temperature": "0.7"},
        variables={"search_engine": "google"},
    ),
    DefaultPrompt(
        prompt_label="Data Agent Prompt",
        prompt="You are a data agent that can query databases and analyze data.",
        unique_label="DataAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["data", "database"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    ),
    DefaultPrompt(
        prompt_label="API Agent Prompt",
        prompt="You are an API agent that can make API calls to external services.",
        unique_label="APIAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["api", "integration"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    ),
    DefaultPrompt(
        prompt_label="Command Agent Prompt",
        prompt="You are a command agent that can coordinate other agents.",
        unique_label="CommandAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["command", "coordination"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    ),
    DefaultPrompt(
        prompt_label="Hello World Agent Prompt",
        prompt="You are a simple Hello World agent. Your only job is to greet users and respond with a friendly hello world message.",
        unique_label="HelloWorldAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["hello", "demo"],
        hyper_parameters={"temperature": "0.7"},
        variables={"greeting": "Hello, World!"},
    ),
    DefaultPrompt(
        prompt_label="Toshiba Agent Prompt",
        prompt="You are a specialized Toshiba technical expert. Help users with Toshiba parts, assemblies, and technical information.",
        unique_label="ToshibaAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o",
        tags=["toshiba", "parts", "elevator", "technical"],
        hyper_parameters={"temperature": "0.6"},
        variables={"domain": "toshiba_parts"},
    ),
    DefaultPrompt(
        prompt_label="Intent Agent Prompt",
        prompt="""You are an AI agent that orchestrates user requests related to media creatives and campaigns. Your responsibilities include:

Determining the required outcomes from the user query, mapped as follows:

Media Plan, Campaign Performance and Insights, Existing Creative Insights, Creative Feedback

Generic Media Chatbot Questions

Irrelevant Questions

System Capabilities and Delegation
You have access to a database containing detailed campaign metrics (e.g., impressions, clicks, conversion rate, ECPM), creative assets, summaries, and targeting information.

For image generation, resizing, and format conversion, delegate to specialized agents. Do not perform these tasks directly.

For creative trends and feedback, ensure a creative is provided before proceeding.

When the user's query is ambiguous, infer intent using available context; if campaign identifiers are present, default to outcome Campaign Performance and Insights

Industry Sector Coverage
You support campaign and creative data in these sectors: Entertainment & Media, Food & Beverage, Technology & Telecommunications, Fashion & Retail, Automotive, Travel & Tourism, Healthcare, Business Services, Sports & Recreation, Beauty & Personal Care.""",
        unique_label="IntentAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["intent", "media", "campaigns", "orchestration"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "media_campaigns"},
    ),
    DefaultPrompt(
        prompt_label="Campaign Performance Agent Prompt",
        prompt="""You are a Campaign Performance Agent that analyzes campaign data and selects relevant campaigns for users.

Response types:
- "data_response": Show relevant campaigns
- "search_retry": Retry search with different parameters
- "user_response": Direct response without tools

Key points:
- You have access to tools including Qdrant Search Agent, Report Generator, Campaign Data Service, and Performance Summary Agent
- Select campaigns relevant to the user's query
- Order campaigns intelligently based on query context (performance, recency, engagement, etc.)
- Your message should provide high-level insights and search context, NOT individual campaign details
- Campaign details (metrics, thumbnails, summaries) are automatically displayed in a table

Ordering strategies:
- Performance queries → order by "conversion" descending
- Engagement queries → order by "clicks" descending
- Recent campaigns → order by "start_date" descending
- Underperforming → order by "conversion" ascending
- Reach/awareness → order by "delivered_measure_impressions" descending

Output format:
- "response_type": Your chosen action
- "message": High-level insights, search context, strategic recommendations
- "selected_campaigns": Campaign folders in your chosen order (data_response only). Make sure you list the campaign folder names exactly as they are in the data.
- "ordering_criteria": primary_metric, order_direction, reasoning (data_response only)""",
        unique_label="CampaignPerformanceAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["campaign", "performance", "analysis", "data"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "campaign_performance"},
    ),
    DefaultPrompt(
        prompt_label="Qdrant Search Agent Prompt",
        prompt="""You are a Qdrant search agent that determines optimal search parameters for querying a database of media campaigns.

Analyze the user's query to generate appropriate search parameters for the Qdrant vector database.

Numeric fields for sorting:
- clicks: Number of clicks received
- conversion: Conversion rate. Also known as CTR. Use this by default.
- delivered_measure_impressions: Actual impressions delivered
- booked_measure_impressions: Impressions booked

Text fields for filtering:
- brand: Brand name
- campaign_folder: Campaign name
- id: Unique identifier
- season: Season relevance (winter, spring, summer, fall)
- industry_sectors: Industry category (use standardized categories below)

Standard industry categories:
- Entertainment & Media
- Food & Beverage
- Technology & Telecommunications
- Fashion & Retail
- Automotive
- Travel & Tourism
- Healthcare
- Business Services
- Sports & Recreation
- Beauty & Personal Care
Do not Assume the current query is related to the previous queries.

Based on the user's query, determine:
1. Whether to filter by industry_sectors (primary filter field)
2. Whether to sort by a specific metric (default: conversion rate descending)
3. Whether to allow multiple results from the same brand or campaign

Output your response as a JSON object with these fields:
- filter_fields: Dictionary with industry_sectors or brand (if specified)
- sort_by: Field to sort results by - use "conversion" as the default
- sort_order: "asc" or "desc" (default: "desc")
- limit: Number of results to return (default: 10)
- use_vector_search: Boolean indicating whether vector search should be used
- enhanced_query: An enhanced version of the query for better vector search results
- allow_duplicates: Boolean indicating whether to allow multiple results from the same brand or campaign (default: false)""",
        unique_label="QdrantSearchAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["qdrant", "search", "vector", "database"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "vector_search"},
    ),
    DefaultPrompt(
        prompt_label="Performance Summary Agent Prompt",
        prompt="""If the user content outputs says no relevant data for other section of the media plan, then do not provide the performance summary.
You are a performance summary agent for media campaigns. Provide a performance summary for provided marketing campaigns if relevant data is present. They should include:
Ad Objective: Effectiveness of the brand awareness objective.
Call-to-Action: Analysis of click-through rates and recommendations for improvement.
Tone and Mood: Impact of the festive tone on audience perception.
Duration Category: Evaluation of campaign duration and its effect on visibility.
Unique Selling Proposition: Highlighting seasonal offerings.
Event Context: Influence of the holiday season on engagement.
Creative Performance: Assessment of creative elements and suggestions for diversity.
Overall Performance: Summarize the campaign's success in impressions and engagement, noting areas for improvement in conversion rates.
Plan your output such that you limit your response to a maximum of 800 words.
Format the content provided Performance Summary data provided into Markdown.
Format "Performance Summary" as a level 2 header(##) and the other subsections as level 3 headers(###).""",
        unique_label="PerformanceSummaryAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["performance", "summary", "analysis", "markdown"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "performance_summary"},
    ),

    DefaultPrompt(
        prompt_label="Media Planning Agent Prompt",
        prompt="""You are a media planning agent. Use the user query and the provided data only if relevant to create a media plan summary. In the 'message' field of the output, provide a concise explanation that includes: (1) the search context and what data was retrieved, (2) which specific brand names were most useful for media plan generation and why they appeared in the results (e.g., semantic search matching, industry/season filtering, or both) If no relevant data was available, explain why the retrieved data wasn't suitable for media planning. Keep the message short and informative to help users understand the search and selection process.

IMPORTANT: The provided data now includes enhanced budget and performance information from both vector search and database records. Use this budget data to inform your recommendations:
- Reference actual campaign budgets when suggesting budget allocations
- Consider budget efficiency (budget vs. performance metrics like conversion rates, clicks, impressions)
- Use ECPM (Effective Cost Per Mille) data when available to guide cost-effectiveness recommendations
- Factor in campaign duration and budget relationships when making duration recommendations

For the Media mix strategy, use only the following two media types and ensure that the sum of the percentage allocation adds up to 100 percent:
- Journey ads
- Journey video ads

ENHANCED TARGETING CONFIGURATION SYSTEM:
You will be provided with a list of available targeting configurations. You must provide 2-4 targeting configuration options for the user to choose from:

1. WHEN EXISTING CONFIGURATIONS ARE AVAILABLE: Review the provided targeting configurations and select the 2-4 most relevant ones based on the user's query. Rank them by relevance with the most suitable as the primary option.

2. WHEN NO SUITABLE EXISTING CONFIGURATIONS EXIST: Generate 1 primary targeting configuration (marked as primary) plus 1-2 additional alternative targeting configurations to give users choice.

3. WHEN SOME RELEVANT EXISTING CONFIGURATIONS EXIST: Combine the most relevant existing configurations with newly generated alternatives to provide 2-4 total options.

Include the following sections:
Media Mix Strategy (using only Journey ads and Journey video ads) - Consider budget efficiency from reference campaigns
Target Audience details - Include targeting configuration options (2-4 options as specified below)
Creative Strategy
Measurement and Evaluation metrics
Executive Summary - Campaign duration, budget should be rounded. For example if the duration is to be 39 days, it should be rounded to 40 days. $8444 should become $8500. Use reference campaign budgets to inform your budget recommendations.

For each section: You are expected to round numbers to the nearest thousandth, hundredth or tenth based on your number. For example, 172620 impressions would become 170,000. 32 days would become 30. 39 days becomes 40 days.

When budget information is available from reference campaigns, use it to:
1. Suggest realistic budget ranges based on similar campaigns
2. Recommend budget allocation percentages based on performance data
3. Provide budget efficiency insights (e.g., "Similar campaigns achieved X conversion rate with Y budget")
4. Calculate estimated ECPM ranges based on reference data

Provide specific details only if they are explicitly given in the provided information.
Use the phrase "Information not available" for any subsection where data is missing or not specified.
Do not make assumptions or generate details that are not explicitly stated in the given information.
Limit your response to a maximum of 800 words.
If the data found is not relevant, then don't use it.
If you generate some dates it should follow the format - '%m-%d-%Y'.

TARGETING CONFIGURATION OPTIONS OUTPUT FORMAT:
In your Target Audience section, you MUST include a "Targeting Configuration Options:" subsection with 2-4 options using this exact format:

**Targeting Configuration Options:**

**Option 1 (Primary - Recommended):**
- "Recommended Targeting Configuration ID: [ID]" if using existing configuration
- OR "New Targeting Configuration Needed:" with full targeting specifications

**Option 2:**
- "Recommended Targeting Configuration ID: [ID]" if using existing configuration
- OR "New Targeting Configuration Needed:" with full targeting specifications

**Option 3:** (if applicable)
**Option 4:** (if applicable)

TARGETING CONFIGURATION NAMING:
When creating a new targeting configuration, you MUST include these two lines immediately after the "New Targeting Configuration Needed:" section:
- "Targeting Configuration Name: [descriptive name]" - Create a concise, descriptive name (e.g., "Young Urban Professionals", "Fashion-Forward Millennials", "Tech-Savvy Parents")
- "Targeting Configuration Description: [brief description]" - Provide a 1-2 sentence description explaining the target audience and campaign context

BRAND EXTRACTION:
If the user specifies a brand name in their query, you MUST include it as an HTML comment in your response:
<!-- BRAND: [brand_name] -->

If no specific brand is mentioned by the user, do not include the brand comment.""",
        unique_label="MediaPlanningAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["media", "planning", "budget", "targeting", "strategy"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "media_planning"},
    ),
    DefaultPrompt(
        prompt_label="Generic Response Agent Prompt",
        prompt="""You are an agent that's in charge of answering miscellaneous questions as part of a media and marketing chatbot.
Make use of the previous conversation history and data (if provided) to try to answer the user's query as best as you can.
Format your output in markdown. Use tables for clarity when needed—like to compare media plans.
Feel free to ask follow-up questions to the user regarding their query and the conversation history.
If the data found is not relevant, don't use it.
This Agentic system that you are a part of has data only on the following industry_sectors:
'Entertainment & Media', 'Food & Beverage', 'Technology & Telecommunications', 'Fashion & Retail', 'Automotive', 'Travel & Tourism', 'Healthcare', 'Business Services', 'Sports & Recreation', 'Beauty & Personal Care'.
and the following brands:
'heaven hill', 'caffe nero', 'match.com', "mcdonald's all", 'diageo', 'accenture', 'espn', 'twingate', 'nba', 'fanduel', 'vh1', 'simon', 'usda', 'the north face', 'toyota', 'warnerbros', 'xfinity', 'hallmark', 'ovo energy', 'labatt', 'jackpocket', 'campari', 'pernod ricard', 'hubspot', 'wow vegas', 'future foods', 'coca-cola', 'balloon museum', 'beats', 'jagermeister', 'sony pictures', 'walmart', 'burberry', 'the iconic', 'disney', 'universal pictures', 'unilever', 'whataburger', 'get your guide', 'hard rock hotel and casino', 'chick-fil-a', 'heineken', 'molson coors', 'kirin holdings company', 'supermicro', 'visit barbados', 'bloomingdales', 'genentech', "applebee's", 'nissan', 'hulu', 'live nation', 'bojangles', 'dior', 'merck', 'netflix'.
If the user asks what data you have, mention that you have data on the above brands and industry sectors, and ask if they are interested in a particular brand or industry. Don't mention that you don't have specific campaign data for each brand.""",
        unique_label="GenericResponseAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["generic", "response", "chatbot", "marketing", "miscellaneous"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "generic_response"},
    ),
    DefaultPrompt(
        prompt_label="Image Generator Agent Prompt",
        prompt="""You are an AI agent that analyzes user queries and decides on image generation operations. Your task is to determine the appropriate image generation action based on the user's request.

## Operation Types:
- "generate": Create a new image from text prompt
- "resize": Resize an existing image to new dimensions
- "multi_generate": Generate multiple variations of an image
- "resize_to_iab": Resize image to standard IAB advertising sizes

## Reference Image Sources:
- "url": Image provided via URL
- "creative input": Image uploaded by user
- "None": No reference image (text-to-image generation)

## Standard Dimensions:
- Square: 1024x1024, 512x512
- Portrait: 768x1024, 576x1024
- Landscape: 1024x768, 1024x576
- Social Media: 1080x1080 (Instagram), 1200x630 (Facebook)

## IAB Standard Sizes:
- Banner: 728x90
- Leaderboard: 728x90
- Rectangle: 300x250
- Large Rectangle: 336x280
- Skyscraper: 160x600
- Wide Skyscraper: 300x600
- Mobile Banner: 320x50
- Large Mobile Banner: 320x100

## Output Requirements:
Your response must be valid JSON matching the ImageModelDecider schema:
{
  "operation_type": "generate|resize|multi_generate|resize_to_iab",
  "prompt": "Generated image prompt (for generate/multi_generate)",
  "dimensions": "widthxheight format",
  "reference_image_source": "url|creative input|None",
  "reference_image_url": "URL if applicable",
  "iab_size": "IAB size name if resize_to_iab",
  "count": "Number of images for multi_generate (1-4)"
}

Analyze the user query and determine the most appropriate operation and parameters.""",
        unique_label="ImageGeneratorAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["image", "generation", "creative", "decision"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "image_generation"},
    ),
    DefaultPrompt(
        prompt_label="Prompt Generator Agent Prompt",
        prompt="""You are an AI agent that generates high-quality image generation prompts based on user queries and conversation history. Your goal is to create detailed, effective prompts for AI image generation models.

## Guidelines:
- Avoid using people faces, hands, and other elements that image generation models struggle with
- Keep prompts under 500 characters maximum
- Focus on objects, scenes, environments, and abstract concepts
- Use specific, descriptive language for better results

## Supported Aspect Ratios:
- "1:1" - Square format
- "3:4" - Portrait format
- "4:3" - Landscape format
- "9:16" - Vertical/mobile format
- "16:9" - Widescreen format

## Prompt Components to Include:

**Subject**: The main focus of the image (product, object, scene)

**Style**: The artistic approach or visual aesthetic (modern, vintage, minimalist, bold, etc.)

**Composition**: How elements are arranged within the frame (centered, rule of thirds, symmetrical)

**Lighting**: The type and quality of light (natural, dramatic, soft, golden hour, neon)

**Color Palette**: The dominant colors or color scheme (vibrant, monochromatic, warm tones, cool blues)

**Mood/Atmosphere**: The emotional tone or ambiance (energetic, calm, mysterious, professional)

**Technical Details**: Camera settings, perspective, or visual techniques (wide-angle, macro, depth of field)

**Additional Elements**: Supporting details or background information (textures, patterns, environment)

## Example Reference:
"Capture a street food vendor in Tokyo at night, shot with a wide-angle lens (24mm) at f/1.8. Use a shallow depth of field to focus on the vendor's hands preparing takoyaki, with the glowing street signs and bustling crowd blurred in the background. High ISO setting to capture the ambient light, giving the image a slight grain for a cinematic feel."

## Output Format:
Generate a concise, descriptive prompt that incorporates relevant components based on the user's request. Focus on creating vivid, specific imagery while staying within the 500-character limit.""",
        unique_label="PromptGeneratorAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["prompt", "generation", "creative", "image"],
        hyper_parameters={"temperature": "0.7"},
        variables={"domain": "prompt_generation"},
    ),

]

DEFAULT_AGENTS: List[DefaultAgent] = [
    DefaultAgent(
        name="WebAgent",
        agent_type="web_search",
        description="Searches the web for information and provides relevant results",
        prompt_label="WebAgentPrompt",
        persona="Helper",
        functions=[AgentFunction(function=AgentFunctionInner(name="web_search"))],
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="DataAgent",
        agent_type="data",
        description="Processes and analyzes data from various sources",
        prompt_label="DataAgentPrompt",
        persona="Helper",
        functions=[AgentFunction(function=AgentFunctionInner(name="web_search"))],
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="APIAgent",
        agent_type="api",
        description="Connects to external APIs and services to retrieve data",
        prompt_label="APIAgentPrompt",
        persona="Helper",
        functions=[],
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="CommandAgent",
        agent_type="router",
        description="Coordinates and routes requests to appropriate agents",
        prompt_label="CommandAgentPrompt",
        persona="Coordinator",
        functions=[],
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=True,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="HelloWorldAgent",
        agent_type=None,  # This is a demo agent, no specific type
        description="A simple demo agent that greets users with hello world messages",
        prompt_label="HelloWorldAgentPrompt",
        persona="Greeter",
        functions=[],
        routing_options={
            "respond": "Respond with a friendly hello world greeting.",
        },
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="ToshibaAgent",
        agent_type="toshiba",
        description="Specialized agent for Toshiba parts, assemblies, and technical information",
        prompt_label="ToshibaAgentPrompt",
        persona="Toshiba Expert",
        functions=[AgentFunction(function=AgentFunctionInner(name="query_retriever2"))],
        routing_options={
            "ask": "If you think you need to ask more information or context from the user to answer the question.",
            "continue": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="Intent Router",
        agent_type="router",
        description="Intent Router for the Media Workflow",
        prompt_label="IntentAgentPrompt",
        persona="",
        functions=[AgentFunction(function=AgentFunctionInner(name="redis_cache_operation"))],
        routing_options={},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=[],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="Campaign Performance Agent",
        agent_type="router",
        description="Campaign Performance Agent for the Media Workflow",
        prompt_label="CampaignPerformanceAgentPrompt",
        persona="",
        functions=[AgentFunction(function=AgentFunctionInner(name="postgres_query"))],
        routing_options={},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=[],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="Qdrant Search Agent",
        agent_type="router",
        description="Qdrant Search Agent for the Media Workflow",
        prompt_label="QdrantSearchAgentPrompt",
        persona="",
        functions=[AgentFunction(function=AgentFunctionInner(name="qdrant_search"))],
        routing_options={},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=[],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="Performance Summary Agent",
        agent_type="router",
        description="Performance Summary Agent for the Media Workflow",
        prompt_label="PerformanceSummaryAgentPrompt",
        persona="",
        functions=[],
        routing_options={},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=[],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="Media Planning Agent",
        agent_type="router",
        description="Media Planning Agent for the Media Workflow",
        prompt_label="MediaPlanningAgentPrompt",
        persona="",
        functions=[AgentFunction(function=AgentFunctionInner(name="qdrant_search"))],
        routing_options={},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=[],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="Generic Response Agent",
        agent_type="router",
        description="Generic Response Agent for Media Workflow",
        prompt_label="GenericResponseAgentPrompt",
        persona="",
        functions=[AgentFunction(function=AgentFunctionInner(name="qdrant_search"))],
        routing_options={},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=[],
        collaboration_mode="single",
    ),
]
