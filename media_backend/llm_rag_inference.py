from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue, MatchAny
from typing import Dict, Any, List
from openai import OpenAI
from model import AdCreative, SearchResult, InferencePayload, ConversationPayload, IntentOutput, MediaPlanOutput, AnalysisOfTrends,CreativeInsightsReport,PerformanceSummary # MediaPlanSearchResult, MediaPlanCreative, CampaignPerformanceReport
import os
import re
from dotenv import load_dotenv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List,Generator, Type, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
import time
import asyncio
from collections import OrderedDict


def timer_decorator(func):
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def load_prompt(prompt_name):
    with open(f'prompts/{prompt_name}.txt', 'r') as file:
        return file.read().strip()

# Load environment variables
load_dotenv()

# Initialize Qdrant client
try:
    Qclient = QdrantClient(
        os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
except Exception as e:
    print(f"Error initializing Qdrant client: {e}")
    Qclient = None

# Initialize OpenAI client
try:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None
@timer_decorator 
def get_embedding(text):
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None
    
@timer_decorator     
def search_qdrant(query_text: str, conversation_payload: list, parameters: Dict[str, Any], use_vector_search: bool = False) -> SearchResult:
    formatted_history = format_conversation_payload(conversation_payload)
    enriched_query_text = f"{formatted_history}\nUser Query: {query_text}"
    
    query_vector = get_embedding(enriched_query_text)
    if not query_vector or len(query_vector) == 0:
        print("No valid query vector obtained from the text.")
        return SearchResult(results=[], total=0)

    if use_vector_search:
        try:
            search_result = Qclient.search(
                collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
                query_vector=query_vector,
                limit=4,  
            )
            print("Pure vector search completed.")
        except Exception as e:
            print(f"Error in vector search: {e}")
            return SearchResult(results=[], total=0)
        ad_creatives = []
        for hit in search_result:
            payload = hit.payload
            try:
                ad_creative = AdCreative.parse_obj(payload)
                ad_creatives.append(ad_creative)
                print(f"Processed result: {payload.get('campaign_folder')}")
            except ValueError as e:
                print(f"Error processing media creative: {e}")
        return SearchResult(results=ad_creatives, total=len(ad_creatives))

    # Build filters for the search
    filter_conditions = []
    numeric_fields = ["file_size", "booked_measure_impressions", "delivered_measure_impressions", "clicks", "conversion", "duration"]
    text_fields = ["file_type", "industry", "targeting", "duration_category", "brand", "season_holiday"]

    def normalize_text(value: str) -> str:
        return value.lower()

    # Add filters for season and holiday
    season = parameters.get('season')
    holiday = parameters.get('holiday')
    if season or holiday:
        season_holiday_values = [item for item in [season, holiday] if item]
        filter_conditions.append(
            FieldCondition(
                key="season_holiday",
                match=MatchAny(any=season_holiday_values)
            )
        )
        print(f"Added season/holiday filter: {season_holiday_values}")

    # Add other filters based on parameters
    for key, value in parameters.items():
        if key in numeric_fields and value is not None:
            filter_conditions.append(
                FieldCondition(key=key, range=Range(gte=float(value)))
            )
            print(f"Added numeric filter for {key}: {value}")
        elif key in text_fields and value:
            normalized_value = normalize_text(value)
            filter_conditions.append(
                FieldCondition(key=key, match=MatchValue(value=normalized_value))
            )
            print(f"Added text filter for {key}: {normalized_value}")

    print("Filter Conditions:", filter_conditions)

    search_filter = Filter(must=filter_conditions) if filter_conditions else None
    print("Search Filter Conditions:", search_filter)

    # Search with filters
    try:
        search_result = Qclient.search(
            collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
            query_vector=query_vector,
            query_filter=search_filter,
            limit=10, 
        )
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        return SearchResult(results=[], total=0)

    print(f"Total results obtained: {len(search_result)}")

    # Process results and create AdCreative instances
    ad_creatives = process_results(search_result)

    return SearchResult(results=ad_creatives, total=len(ad_creatives))

def process_results(search_result) -> List[AdCreative]:
    ad_creatives = []
    brands_seen = set()
    for hit in search_result:
        print("hit.scores:", hit.score)
        if hit.score <= 0.79:
            break  # Stop processing if score below threshold
        payload = hit.payload
        try:
            ad_creative = AdCreative.parse_obj(payload)
            brand = ad_creative.brand.lower()
            if brand not in brands_seen:
                ad_creatives.append(ad_creative)
                brands_seen.add(brand)
                print(f"Processed result with score {hit.score}: {payload.get('campaign_folder')} (Brand: {brand})")
                if len(ad_creatives) == 5:
                    break
        except ValueError as e:
            print(f"Error processing media creative: {e}")
    
    print(f"Number of results after processing: {len(ad_creatives)}")
    return ad_creatives

@timer_decorator   
def determine_intent(user_query: str, conversation_history: List[ConversationPayload]) -> dict:
    try:
        prompt1 = load_prompt('intent')
        messages = [{"role": "system", "content": prompt1}]
        
        for message in conversation_history:
            messages.append({"role": message.actor, "content": message.content})
        
        messages.append({"role": "user", "content": user_query})
        
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            # response_format=IntentOutput,
            max_tokens=400
        )
        
        response_content = response.choices[0].message.content
        # print(f"Response content: {response_content}")  # Log response content for debugging
        
        try:
            parsed_response = json.loads(response_content)
            validated_response = IntentOutput(**parsed_response)
            return validated_response.model_dump()  # Ensure this method exists
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {json_error}")
            return {"error": "Failed to parse JSON response"}
        except ValueError as validation_error:
            print(f"Validation error: {validation_error}")
            return {"error": "Response did not match expected format"}
        
    except Exception as e:
        print(f"Error determining intent: {e}")
        print("Query that led to error:", user_query)
        return {}
@timer_decorator   
def format_search_results(search_result: SearchResult) -> str:
    formatted_results = []
    print("Formatting the search results")
    for ad in search_result.results:
        formatted_ad = f"ID: {ad.id}\n"
        formatted_ad += f"Brand: {ad.brand}\n"
        formatted_ad += f"Product/Service: {ad.product_service}\n"
        formatted_ad += f"Objective: {ad.ad_objective}\n"
        formatted_ad += f"Tone/Mood: {ad.tone_mood}\n"
        formatted_ad += f"File Type: {ad.file_type}\n"
        formatted_ad += f"Industry: {ad.industry}\n"
        formatted_ad += f"Duration Category: {ad.duration_category}\n"
        formatted_ad += f"Impressions: {ad.delivered_measure_impressions}\n"
        formatted_ad += f"Clicks: {ad.clicks}\n"
        formatted_ad += f"Conversions: {ad.conversion}\n"
        formatted_ad += f"Md5_hash:{ad.md5_hash}"  # Include the image
        formatted_ad += f"File Name:{ad.file_name}"
        formatted_ad += "---"
        formatted_results.append(formatted_ad)
    print("Sucesss fully completed format search")
    return "\n".join(formatted_results)

@timer_decorator
async def generate_response(
    query: str,
    system_prompt: str,
    search_result: str = None,
    conversation_history: List[ConversationPayload] = None,
    combined_output: str = None,
    output_parts: Dict[str, str] = None,
    max_tokens: int = 2400, 
    response_class: Optional[Type[BaseModel]] = None,
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    if search_result:
        messages.append({"role": "system", "content": f"Search Results: {search_result}"})
    if conversation_history:
        for message in conversation_history:
            messages.append({"role": message.actor, "content": message.content})
    
    messages.append({"role": "user", "content": f"Query: {query}"})
    if output_parts:
        for key, value in output_parts.items():
            messages.append({"role": "user", "content": f"{key.capitalize()}: {value}"})

    if combined_output:
        messages.append({"role": "user", "content": f"Combined Output: {combined_output}"})

    try:
        request_params = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": max_tokens,
            "n": 1,
            "temperature": 0.1
        }
        if response_class:
            request_params["response_format"] = response_class

        # total_tokens = len(str(request_params))
        # print("Total tokens before request:", total_tokens)

        response = await asyncio.to_thread(client.beta.chat.completions.parse, **request_params)

        response_content = response.choices[0].message.content.strip()
        total_tokens = response.usage.total_tokens
        # print("total tokens used:", total_tokens)
        if response_class:
            try:
                response_class.model_validate_json(response_content)
            except Exception as validation_error:
                print(f"Warning: Response validation failed: {validation_error}")
                print("Returning raw response string.")
        return response_content
    except Exception as e:
        print(f"Error in generating response: {e} at the response class: {system_prompt}")
        return "I apologize, but I couldn't generate a response at this time."

@timer_decorator   
async def formatter(final_output: str = None, prompt_file_name: str = "formatter",query_content:str=None) -> str:
    system_prompt = load_prompt(prompt_file_name)
    query = f"Content to be formatted: {final_output}"
    if query_content:
        query += f"Original Query:{query_content}"
    formatted_output = await generate_response(
        query=query,
        system_prompt=system_prompt,
        max_tokens=4000
    )
    return "\n"+formatted_output+"\n"
@timer_decorator 
def extract_specific_fields(search_result: SearchResult, fields: List[str], full_data_fields: List[str] = None) -> str:
    extracted_data = []
    for ad_creative in search_result.results:
        item = {}
        # Extract specified fields from AdCreative
        for field in fields:
            if hasattr(ad_creative, field):
                item[field] = getattr(ad_creative, field)
        # Extract specified fields from full_data
        if full_data_fields and ad_creative.full_data:
            for field in full_data_fields:
                if field in ad_creative.full_data:
                    item[f"full_data_{field}"] = ad_creative.full_data[field]
        extracted_data.append(item)
    return str(extracted_data)

@timer_decorator    
async def media_plan(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
    # Media_plan Data filtered out
    fields_to_extract = [
    "ad_objective",
    "duration(days)",
    "duration_category",
    "tone_mood",
    "booked_measure_impressions",
    "delivered_measure_impressions",
    "conversion",
    ]
    full_data_fields_to_extract = [
    "target market",
    "target audience",
    "weekends",
    "holidays",
    "national events",
    "sport events",
    "strategy",
    "visual elements",
    "imagery",
    "targeting",
    "industry",
    ]
    essential_data = extract_specific_fields(filtered_data,fields_to_extract,full_data_fields_to_extract)

    system_prompt = load_prompt("media_plan")
    # print("media plan Input len:",len(query)+len(system_prompt)+len(essential_data)+len(conversation_history))
    # print("Query, system, filtered, convo history:",len(query),len(system_prompt),len(essential_data),len(conversation_history))
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=MediaPlanOutput,
        max_tokens=2500,
    )
    print("Media_plan Raw text:",raw_response)
    return await formatter(raw_response,"formatter_media_plan",query)

@timer_decorator
async def campaign_performance(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
    fields_to_extract = [
        "brand",
        "ad_objective",
        "duration(days)",
        "duration_category",
        "delivered_measure_impressions",
        "clicks",
        "conversion",
        "md5_hash",
        "tone_mood",
        "imagery",
        "file_name",
    ]
    full_data_fields_to_extract = [
        "product/service",
    ]
    
    essential_data = extract_specific_fields(filtered_data, fields_to_extract, full_data_fields_to_extract)

    system_prompt = load_prompt("formatter_campaign_performance")

    print("Campaign performance inputs: ",str(query)+str(system_prompt)+str(essential_data))
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        # response_class=CampaignPerformanceReport,
        max_tokens=4000
    )
    return raw_response
@timer_decorator
async def analysis_of_trends(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
    fields_to_extract = [
        "brand",
        "industry",
        "ad_objective",
        "tone_mood",
        "duration(days)",
        "duration_category",
        "targeting"
        "booked_measure_impressions",
        "conversion",
        "file_type",
        "type",
    ]
    full_data_fields_to_extract = [
        "call-to-action",
        "strategy",
        "weekends",
        "holidays",
        "national events",
        "sport events",
        "visual elements",
        "imagery",
    ]
    
    # Assuming extract_specific_fields is a quick operation, keep it synchronous
    essential_data = extract_specific_fields(filtered_data, fields_to_extract, full_data_fields_to_extract)

    # Assuming load_prompt is a quick operation, keep it synchronous
    system_prompt = load_prompt("analysis_of_trends")
    
    # print("analysis Input len:", len(query) + len(system_prompt) + len(essential_data) + len(conversation_history))
    
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=AnalysisOfTrends
    )
    
    print("Analysis of trends raw text:", raw_response)

    formatted_response = await formatter(raw_response, "formatter_analysis_of_trends")
    
    return formatted_response

@timer_decorator
async def creative_insights(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
    fields_to_extract = [
        "brand",
        "ad_objective",
        "tone_mood",
        "md5_hash",
        "colors",
        "duration(days)",
        "duration_category",
        "imagery",
        "file_name",
    ]
    full_data_fields_to_extract = [
        "product/service",
        "call-to-action",
        "strategy",
        "visual elements",
        "cinematography",
        "audio elements",
        "narrative structure",
        "weekends",
        "holidays",
        "national events",
        "sport events",
    ]
    
    # Assuming extract_specific_fields is a quick operation, keep it synchronous
    essential_data = extract_specific_fields(filtered_data, fields_to_extract, full_data_fields_to_extract)

    # Assuming load_prompt is a quick operation, keep it synchronous
    system_prompt = load_prompt("creative_insights")
    
    print("creative insight Input:",essential_data)
    
    # Use the async version of generate_response
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=CreativeInsightsReport
    )
    print("Creative Insights Raw:", (raw_response))
    formatted_response = await formatter(raw_response, "formatter_creative_insights")
    return formatted_response

@timer_decorator
async def performance_summary(query: str, output_parts: Dict[str, str]) -> str:
    # Assuming load_prompt is a quick operation, keep it synchronous
    system_prompt = load_prompt("performance_summary")
    
    # print("performance summary Input len:", len(query) + len(system_prompt) + len(str(output_parts)))
    
    # Use the async version of generate_response
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        output_parts=output_parts,
        response_class=PerformanceSummary
    )
    # print("Performance summary len:", len(raw_response))
    # Use the async version of formatter
    formatted_response = await formatter(raw_response, "formatter_performance_summary")
    return formatted_response


@timer_decorator
def replace_hash_with_url(S):
    md5_pattern_thumbnail = r'\b([a-fA-F0-9]{32})(?:\.thumbnail\.jpg)?\b'
    # openMediaModal_pattern = r"openMediaModal\('([a-fA-F0-9]{32})'"

    def replace_thumbnail(match):
        hash_value = match.group(1)
        return get_url_for_hash(hash_value, "thumbnail.jpg")

    # def replace_openMediaModal(match):
    #     hash_value = match.group(1)
    #     file_extension = get_extension_for_hash(hash_value)
    #     return f"openMediaModal('{get_url_for_hash(hash_value, file_extension)}'"

    # Replace thumbnail URLs
    S = re.sub(md5_pattern_thumbnail, replace_thumbnail, S)
    # # Replace openMediaModal hashes
    # S = re.sub(openMediaModal_pattern, replace_openMediaModal, S)
    return S
@timer_decorator 
def get_url_for_hash(hash, extension):
    base_url = "http://127.0.0.1:8000/static/images"
    directory_structure = f"{hash[:2]}/{hash[2:4]}/{hash}"
    return f"{base_url}/{directory_structure}.{extension}"
@timer_decorator 
def get_extension_for_hash(hash):
    # Use forward slashes for cross-platform compatibility
    base_path = "static/images"  # Change to your actual path
    extensions = ['jpg', 'mov', 'png', 'gif', 'mp4']
    # Construct the directory structure using os.path.join
    directory_structure = os.path.join(base_path, hash[:2], hash[2:4])
    for ext in extensions:
        file_path = os.path.join(directory_structure, f"{hash}.{ext}")
        file_path = os.path.normpath(file_path)  # Normalize the path
        # print(f"Checking: {file_path}")  # Debug line
        if os.path.isfile(file_path):
            return ext

    return "unknown"  # or raise an exception if preferred

def remove_markdown_prefix(s):
    s = re.sub(r'```markdown', '', s)
    s = re.sub(r'```', '\n---', s)
    # s = re.sub(r'### (.*)\n', r'<h2><strong>\1</strong></h2><br>\n', s)
    # s = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', s)
    return s
@timer_decorator 
def format_conversation_payload(conversation_payload: List[ConversationPayload]) -> str:
    # Format the conversation history into a single string
    formatted_history = ""
    for entry in conversation_payload:
        actor = entry.actor
        content = entry.content
        formatted_history += f"{actor}: {content}\n"
    return formatted_history.strip()

@timer_decorator
async def perform_inference(inference_payload: InferencePayload):
    try:
        conversation_history = inference_payload.conversation_payload or []
        intent_data = determine_intent(inference_payload.query, conversation_history)
        print("Intent:", intent_data)

        # if not intent_data:
        #     print("Retrying Intent\n")
        #     intent_data = determine_intent(inference_payload.query, conversation_history)

        required_outcomes = intent_data.get('required_outcomes', [])
        unrelated_query = intent_data.get('unrelated_query',False)

        if unrelated_query:
            conversation_history = ""

        if not required_outcomes:
            yield {"response": "I apologize, but I'm not able to help with that request. I specialize in media marketing campaigns plan generation and historical data insights. Is there anything related to media campaigns that I can assist you with?\n"}
            return
        
        parameters = intent_data.get('parameters', {}) 
        filtered_data = search_qdrant(inference_payload.query, conversation_history, parameters)

        # if not filtered_data.results:
        #     yield {"response": "I couldn't find any relevant information based on your query. Could you please rephrase or provide more details?\n"}
        #     return
        
        if not filtered_data.results:
            yield {"response":"I'm sorry, but I lack infromation on media campaigns related to your query. However I can respond to your query using campaign data most related with your query."}
            filtered_data = search_qdrant(inference_payload.query, conversation_history, parameters, use_vector_search=True)

        output_parts = OrderedDict()
        ordered_keys = ["media_plan", "analysis_of_trends", "campaign_performance", "creative_insights", "performance_summary"]

        for outcome in required_outcomes:
            if outcome in [1, 2, 3, 4]:
                insight_function = await get_insight_function(outcome)
                result = await insight_function(filtered_data, inference_payload.query, conversation_history)
                # print("Before:",result)
                result = replace_hash_with_url(remove_markdown_prefix(result))
                # print("After",result)
                output_parts[ordered_keys[outcome - 1]] = result
                # print(f"Completed outcome {outcome}: {result}")
                yield {"response": result}  # Stream response

        # Process performance_summary if needed
        if 5 in required_outcomes:
            performance_summary_result = await performance_summary(inference_payload.query, output_parts)
            performance_summary_result = replace_hash_with_url(remove_markdown_prefix(performance_summary_result))
            output_parts["performance_summary"] = performance_summary_result
            yield {"response": f"{performance_summary_result}\n\n"}

    except Exception as e:
        print("An error occurred:", e)
        yield {"response": f"An error occurred: {e}\n"}

@timer_decorator 
async def get_insight_function(outcome):
    """ Maps required outcomes to their corresponding async functions. """
    mapping = {
        1: media_plan,          
        2: analysis_of_trends, 
        3: campaign_performance,
        4: creative_insights,
        5: performance_summary,
    }
    return mapping.get(outcome)
