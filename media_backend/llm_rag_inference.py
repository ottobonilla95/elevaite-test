from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue, MatchAny
from fastapi import HTTPException
from typing import Dict, Any, List
from openai import OpenAI
from model import AdCreative, SearchResult, InferencePayload, ConversationPayload, IntentOutput, MediaPlanOutput, AnalysisOfTrends,CreativeInsightsReport,PerformanceSummary # MediaPlanSearchResult, MediaPlanCreative, CampaignPerformanceReport
import os
import re
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import json
from typing import List, Type, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
import time
import requests
import asyncio
from collections import OrderedDict

import logging
# Timer and logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timer_decorator(func):
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        logger.info(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.info(f"{func.__name__} took {end - start:.6f} seconds")
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
    logger.error(f"Error initializing Qdrant client: {e}")
    Qclient = None

# Initialize OpenAI client
try:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}")
    client = None
# @timer_decorator 
def get_embedding(text):
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return None

# Searches Qdrant and returns search result object
def search_qdrant(query_text: str, conversation_payload: list, parameters: Dict[str, Any], use_vector_search: bool = False, number_of_results: int = 4) -> SearchResult:
    formatted_history = format_conversation_payload(conversation_payload)
    enriched_query_text = f"{formatted_history}\nUser Query: {query_text}"
    query_vector = get_embedding(enriched_query_text)

    if not query_vector or len(query_vector) == 0:
        logger.error("No valid query vector obtained from the text.")
        return SearchResult(results=[], total=0)

    ad_creatives = []

    # If vector search is to be performed
    if use_vector_search:
        brand_count = {}  # Dictionary to count creatives per brand
        try:
            search_result = Qclient.search(
                collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
                query_vector=query_vector,
                limit=number_of_results,
            )
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return SearchResult(results=[], total=0)

        # Process vector search results
        # print("SEARCH RESULTS:",search_result)
        for hit in search_result:
            if hit.score > 0.70: # Magic number
                try:
                    # print("Vector search score:", hit.score)
                    ad_creative = AdCreative.parse_obj(hit.payload)
                    brand_name = ad_creative.brand
                    if brand_name not in brand_count:
                        brand_count[brand_name] = 0
                    if brand_count[brand_name] < 2:  # Limit to 2 per brand
                        ad_creatives.append(ad_creative)
                        brand_count[brand_name] += 1
                    else:
                        logger.info(f"Skipped AdCreative for brand: {brand_name}")
                except Exception as e:
                    logger.error(f"Error processing vector search result: {e}, Data: {hit}")

    # Build filters for the search if not using vector search
    if not use_vector_search:
        filter_conditions = []
        numeric_fields = ["file_size", "booked_measure_impressions", "delivered_measure_impressions", "clicks", "conversion", "duration"]
        text_fields = ["file_type", "industry", "targeting", "duration_category", "brand", "season_holiday"]

        def normalize_text(value: str) -> str:
            return value.lower()

        # Add filters for season and holiday
        # print("before the filters:")
        if parameters:
            season = parameters.get('season','')
            holiday = parameters.get('holiday','')
            if season or holiday:
                season_holiday_values = [item for item in [season, holiday] if item]
                filter_conditions.append(
                    FieldCondition(
                        key="season_holiday",
                        match=MatchAny(any=season_holiday_values)
                    )
                )

            # Add other filters based on parameters
            for key, value in parameters.items():
                if key in numeric_fields and value is not None:
                    filter_conditions.append(
                        FieldCondition(key=key, range=Range(gte=float(value)))
                    )
                elif key in text_fields and value:
                    normalized_value = normalize_text(value)
                    filter_conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=normalized_value))
                    )

            search_filter = Filter(should=filter_conditions) if filter_conditions else None

            try:
                search_result = Qclient.search(
                    collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
                    query_vector = query_vector,
                    query_filter=search_filter,
                    limit=number_of_results,
                )
            except Exception as e:
                logger.error(f"Error searching Qdrant: {e}")
                return SearchResult(results=[], total=0)
            
            # Process filtered search results with brand limit
            brand_count = {}
            for index, hit in enumerate(search_result):
                if hit.score>0.78: # Magic Number
                    try:
                        # print("Filtered score:",hit.score)
                        payload = hit.payload
                        ad_creative = AdCreative.parse_obj(payload)
                        brand_name = ad_creative.brand
                        if brand_name not in brand_count:
                            brand_count[brand_name] = 0
                        if brand_count[brand_name] < 2:  # Limit to 2 per brand
                            ad_creatives.append(ad_creative)
                            brand_count[brand_name] += 1
                        else:
                            logger.info(f"Skipped AdCreative for brand: {brand_name}")
                    except ValueError as e:
                        logger.error(f"Error processing media creative {index + 1}: {e}")
                        logger.error(f"Problematic payload: {payload}")

    logger.info(f"Total AdCreatives processed: {len(ad_creatives)}")
    return SearchResult(results=ad_creatives, total=len(ad_creatives))

# Identifies the intent and enhances the query
@timer_decorator   
def determine_intent(user_query: str, conversation_history: List[ConversationPayload],prompt_file: str,creative_provided: bool = False) -> dict:
    try:

        system_prompt = load_prompt(prompt_file)
        if creative_provided:
            system_prompt += "A creative was provided for this query.\n"

        messages = [{"role": "system", "content": system_prompt}]
        for message in conversation_history:
            messages.append({"role": message.actor, "content": message.content})
        
        messages.append({"role": "user", "content": user_query})
        
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=IntentOutput,
            max_tokens=500
        )
        # print("output responsee",response)
        response_content = response.choices[0].message.content
        try:
            parsed_response = json.loads(response_content)
            validated_response = IntentOutput(**parsed_response)
            return validated_response.model_dump()  # Ensure this method exists
        except json.JSONDecodeError as json_error:
            logger.error(f"JSON parsing error: {json_error}")
            return {"error": "Failed to parse JSON response"}
        except ValueError as validation_error:
            logger.error(f"Validation error: {validation_error}")
            return {"error": "Response did not match expected format"}
        
    except Exception as e:
        logger.error(f"Error determining intent: {e}")
        logger.error(f"Query that led to error:{user_query}")
        return {"error": "Error determining intent"}

async def generate_response_streaming(
    query: str,
    system_prompt: str,
    search_result: str = None,
    conversation_history: List[ConversationPayload] = None,
    combined_output: str = None,
    output_parts: Dict[str, str] = None,
    max_tokens: int = 2400,
) -> AsyncGenerator[str, None]:
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
            "temperature": 0.1,
            "stream": True  # Enable streaming
        }
        response_stream = client.chat.completions.create(**request_params)
        for chunk in response_stream:
            content = chunk.choices[0].delta.content
            # print("streamed content:",content)
            yield content
    except Exception as e:
        logger.error(f"Error in generating response: {e}")
        yield f"Error: {str(e)}"


# @timer_decorator
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
        response = await asyncio.to_thread(client.beta.chat.completions.parse, **request_params)
        response_content = response.choices[0].message.content.strip()
        if response_class:
            try:
                response_class.model_validate_json(response_content)
            except Exception as validation_error:
                logger.error(f"Warning: Response validation failed: {validation_error}")
              ##  logger.debug("Returning raw response string.")
        return response_content
    except Exception as e:
        logger.error(f"Error in generating response: {e} at the response class: {system_prompt}")
        return "I apologize, but I couldn't generate a response at this time."

# @timer_decorator
def generate_response_with_creatives(    
    creative :str, # Base 64 encoded image/video/gif
    query: str,
    system_prompt: str,
    search_result: str = None,
    conversation_history: List[ConversationPayload] = None,
    combined_output: str = None,
    output_parts: Dict[str, str] = None,
    max_tokens: int = 2400, 
    response_class: Optional[Type[BaseModel]] = None,):
    
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

    if creative:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Here is the creative content."},
                {"type": "image_url", "image_url": {"url": f"{creative}"}}
            ]
        })
    try:
        request_params = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": max_tokens,
            "n": 1,
            "temperature": 0.1,
        }
        # print("Message sent:",request_params)
        if response_class:
            request_params["response_format"] = response_class
        response = client.chat.completions.create(**request_params)
        # print("Response:",response)
        response_content = response.choices[0].message.content.strip()        
        if response_class:
            try:
                response_class.model_validate_json(response_content)
            except Exception as validation_error:
                logger.error(f"Warning: Response validation failed: {validation_error}")
        return response_content
    except Exception as e:
            logger.error(f"Error in generating response: {e} during the process with the system prompt: {system_prompt}")
    return 
    
@timer_decorator
def creative_to_features(creative: str)-> str:
    prompt = load_prompt("creative_feature_extractor")
    messages = [{"role": "system", "content": prompt}]
    messages.append({"role":"user","content":[{
                        "type": "image_url",
                        "image_url": {"url": creative}}]})
    try:
        request_params = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 300,
            "n": 1,
            "temperature": 0.1,
        }
        response = client.chat.completions.create(**request_params)
        response_content = response.choices[0].message.content.strip()
        return response_content
    except Exception as e:
            logger.error(f"Error in generating response: {e} during the process with the prompt: {prompt}")
    return

# @timer_decorator
def generate_image_from_getimgai(prompt: str, image_data: Optional[str] = None, api_call_type: str = "text-to-image", model: str = "flux-schnell"):
    
    # Determine if it's an image-to-image request
    if api_call_type == "image-to-image":
        is_image_to_image = True
    else:
        is_image_to_image = False

    # If it's image-to-image and no image data is provided, raise an error
    if is_image_to_image and image_data is None:
        raise HTTPException(status_code=400, detail="For image-to-image, initial image data is required.")
    
    # If it's image-to-image and the model is flux-schnell, adjust the model to stable-diffusion-xl
    if is_image_to_image:
        if model == "flux-schnell":
            model = "stable-diffusion-xl"

    url = f"https://api.getimg.ai/v1/{model}/{api_call_type}"

    # Headers for the API request
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {os.getenv('GETIMGAI_API_KEY')}"
    }

    # Prepare the payload for the API request
    if model == "stable-diffusion-xl":
        payload = {
            "prompt": prompt,
            "response_format": "url",  # Asking for the URL format of the result
            "num_images": 1,
            "width": 1024,
            "steps": 20,
            "height": 1024,
        }
    elif model == "flux-schnell":
        payload = {
            "prompt": prompt,
            "response_format": "url",  # Asking for the URL format of the result
            "width": 1024,
            "steps": 4,
            "height": 1024,
        }

    # If it's an image-to-image request, decode the base64 image data
    if is_image_to_image:
        try:
            # Check if the base64 string includes the mime type and image data
            match = re.match(r"^data:image/(png|jpeg|jpg);base64,", image_data)
            if not match:
                raise HTTPException(status_code=400, detail="Invalid base64 image format. Ensure the image is properly base64-encoded with the correct mime type (image/png, image/jpeg).")

            # Extract MIME type (png, jpeg, jpg)
            mime_type = match.group(1)
            if mime_type == "png":
                mime_type = "image/png"
            elif mime_type in ["jpeg", "jpg"]:
                mime_type = "image/jpeg"

            # The base64 string without the MIME type prefix
            image_data_cleaned = image_data.split(",")[1]
            
            # Now we can include the base64 string directly in the payload
            payload["image"] = image_data_cleaned  # Adding the base64 string to the payload

        except Exception as e:
            raise HTTPException(status_code=400, detail="Error processing image data. Ensure it's a valid base64-encoded image.")

    # Make the API request (POST)
    response = requests.post(url, headers=headers, json=payload)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Error Response: {response.text}")  # Log the full response body for debugging
        raise HTTPException(status_code=response.status_code, detail="Error generating image")
    
    # Parse the response JSON to get the image URL
    response_data = response.json()
    
    image_url = response_data.get('url', None)
    if not image_url:
        print(f"API Response did not return expected image URL: {response.json()}")
        raise HTTPException(status_code=500, detail="Image URL not found in response")
    
    output = f"""\n\n## Generated Image \n ![Image Generated]({image_url} "Generated Images")\n"""
    return output
@timer_decorator
async def creative_inspiration_with_generation(
    enhanced_query: str, 
    creative: str = "",
    conversation_history: List[ConversationPayload] = None, 
    vector_search: bool = False,
    image_data: Optional[bytes] = None,
):
    if not conversation_history:
        conversation_history = ""
    search_results = ""
    if creative:
        extracted_features = creative_to_features(creative)
        # print("Extracted features:",extracted_features)
    if creative and vector_search:
        search_results = search_qdrant(f"{enhanced_query} Creative: {extracted_features}", conversation_history, use_vector_search=True, number_of_results=3,parameters={})
    elif vector_search:
        search_results = search_qdrant(f"{enhanced_query}", conversation_history, use_vector_search=True, number_of_results=3,parameters={})
    
    system_prompt = load_prompt("creative_agent_generation")
    # print(system_prompt)
    if creative:
        generated_prompt = await generate_response(query=f"{enhanced_query} Attached Creatives Features:{extracted_features}", system_prompt=system_prompt, search_result=search_results, conversation_history=conversation_history,max_tokens=1048)
    else:
        generated_prompt = await generate_response(query=enhanced_query, system_prompt=system_prompt, search_result=search_results, conversation_history=conversation_history,max_tokens=1048)
    # print("Generated prompt:",generated_prompt)
    logger.info(f"Generated prompt:\n{generated_prompt}")
    if creative:
        image_data = generate_image_from_getimgai(prompt=generated_prompt, api_call_type="text-to-image",model="flux-schnell")
    else:
        image_data = generate_image_from_getimgai(prompt=generated_prompt, api_call_type="text-to-image",model="flux-schnell")
    return image_data

@timer_decorator
def ideate_to_create_with_rag(user_query: str,creative:str,conversation_history:List[ConversationPayload],parameters:Dict[str, Any])-> str:
    extracted_features = creative_to_features(creative)
    search_result = search_qdrant(query_text= f"{user_query} Creatives: {extracted_features}", conversation_payload=conversation_history,parameters=parameters,use_vector_search = True, number_of_results = 2)
    # print("Search Results :",search_result)
    prompt = load_prompt("creative_trends")
    return generate_response_with_creatives(creative=creative,query=user_query,search_result=search_result,system_prompt=prompt,conversation_history=conversation_history) 

@timer_decorator
def ideate_to_create_without_rag(user_query:str,creative:str,conversation_history:List[ConversationPayload])-> str:
    prompt = load_prompt("creative_feedback")
    return generate_response_with_creatives(creative=creative,query=user_query,system_prompt=prompt,conversation_history=conversation_history) 

# @timer_decorator
async def formatter_streaming(final_output: str = None, prompt_file_name: str = "formatter", query_content: str = None) -> AsyncGenerator[str, None]:
    system_prompt = load_prompt(prompt_file_name)
    query = f"Content to be formatted: {final_output}"
    if query_content:
        query += f"\nOriginal Query: {query_content}"
    # Use the streaming response generator
    async for chunk in generate_response_streaming(
        query=query,
        system_prompt=system_prompt,
        max_tokens=4000
    ):
        yield chunk

# @timer_decorator   
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

# @timer_decorator 
def extract_specific_fields(search_result: SearchResult, fields: List[str], full_data_fields: List[str] = None) -> str:
    extracted_data = []
  ##  logger.debug(f"Search Results:\n\n{search_result}")
    for ad_creative in search_result.results:
        # print(ad_creative)
        item = {}
        # Extract specified fields from AdCreative
        for field in fields:
            if hasattr(ad_creative, field):
                item[field] = getattr(ad_creative, field)
        # Extract specified fields from full_data
        if full_data_fields and ad_creative.full_data:
            for field in full_data_fields:
                normalized_field = field.replace(' ', '_')
                if normalized_field in ad_creative.full_data:
                    item[f"full_data_{normalized_field}"] = ad_creative.full_data[normalized_field]
                #     print(f"Extracting: {field}")
                # else:
                #     print(f"Didn't find: {field}")
        
        extracted_data.append(item)
    
    return str(extracted_data)
@timer_decorator    
async def media_plan(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) ->  AsyncGenerator[str, None]:
    # Media_plan Data filtered out
    fields_to_extract = [
    "ad_objective",
    "duration(days)",
    "duration_category",
    "tone_mood",
    "booked_measure_impressions",
    "delivered_measure_impressions",
    "budget",
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
    # logger.debug("media plan Input len:",len(query)+len(system_prompt)+len(essential_data)+len(conversation_history))
    # logger.debug("Query, system, filtered, convo history:",len(query),len(system_prompt),len(essential_data),len(conversation_history))
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=MediaPlanOutput,
        max_tokens=2500,
    )
  ##  logger.debug(f"Media_plan Raw text:{raw_response}")
    async for chunk in formatter_streaming(raw_response, "formatter_media_plan", query):
            yield chunk
    # return await formatter(raw_response,"formatter_media_plan",query)

@timer_decorator
async def campaign_performance(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
    fields_to_extract = [
        "brand",
        "ad_objective",
        "duration(days)",
        "duration_category",
        "delivered_measure_impressions",
        "booked_measure_impressions",
        "clicks",
        "conversion",
        "md5_hash",
        "tone_mood",
        "imagery",
        "file_name",
        "budget",
    ]
    full_data_fields_to_extract = [
        "product/service",
    ]
    
    essential_data = extract_specific_fields(filtered_data, fields_to_extract, full_data_fields_to_extract)

    system_prompt = load_prompt("campaign_performance_with_formatter")

    # logger.debug("Campaign performance inputs: ",str(query)+str(system_prompt)+str(essential_data))
    # print("Extracted data campaign performance:",essential_data)
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
    
    # print("analysis Input:", query, system_prompt,essential_data)
    
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=AnalysisOfTrends
    )
    # logger.debug("Analysis of trends raw text:", raw_response)

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
    
    # print(f"creative insight Input:{essential_data}; prompt: {system_prompt};Conversation:{conversation_history},response_class:{CreativeInsightsReport},query:{query}")
    
    # Use the async version of generate_response
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=CreativeInsightsReport
    )
  #  logger.debug(f"Creative Insights Raw: {raw_response}")
    # print(f"raw_response: {raw_response}")
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
        # response_class=PerformanceSummary
    )
    # print("Performance summary len:", len(raw_response))
    # Use the async version of formatter
    # formatted_response = await formatter(raw_response, "formatter_performance_summary")
    return f"""\n\n{raw_response}"""

@timer_decorator
async def generic_without_creative(query: str, conversation_history: List[ConversationPayload],filtered_data: SearchResult=None):
    system_prompt = load_prompt("generic")    
    if filtered_data:

        raw_response = await generate_response(query=query,system_prompt=system_prompt,conversation_history=conversation_history,search_result=filtered_data)
    else:
        raw_response = await generate_response(query=query,system_prompt=system_prompt,conversation_history=conversation_history,)
    return raw_response

@timer_decorator
def generic_with_creative(user_query:str,conversation_history:List[ConversationPayload],creative:str,filtered_data: SearchResult=None)-> str:
    prompt = "You are an AI assistant. Be Polite and answer in markdown. You can answer questions based on uploaded creatives."
    if filtered_data:
        result = generate_response_with_creatives(creative=creative,query=user_query,system_prompt=prompt,conversation_history=conversation_history,search_result=filtered_data) 
    else:
        result = generate_response_with_creatives(creative=creative,query=user_query,system_prompt=prompt,conversation_history=conversation_history) 
    return result

# @timer_decorator
def replace_hash_with_url(S):
    md5_pattern_thumbnail = r'\b([a-fA-F0-9]{32})(?:\.thumbnail\.jpg)?\b'
    def replace_thumbnail(match):
        hash_value = match.group(1)
        return get_url_for_hash(hash_value, "thumbnail.jpg")
    # Replace thumbnail URLs
    S = re.sub(md5_pattern_thumbnail, replace_thumbnail, S)

    return S
# @timer_decorator 
def get_url_for_hash(hash, extension):
    base_url = os.getenv("BASE_URL_FOR_CREATIVES")
    directory_structure = f"{hash[:2]}/{hash[2:4]}/{hash}"
    return f"{base_url}/{directory_structure}.{extension}"
# @timer_decorator 
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
# @timer_decorator 
def format_conversation_payload(conversation_payload: List[ConversationPayload]) -> str:
    # Format the conversation history into a single string
    formatted_history = ""
    for entry in conversation_payload:
        actor = entry.actor
        content = entry.content
        formatted_history += f"{actor}: {content}\n"
    return formatted_history.strip()



# @timer_decorator
async def perform_inference(inference_payload: InferencePayload):
    try:
        threshold = 3
        conversation_history = inference_payload.conversation_payload or []

        logger.info(f"conversation_history:{conversation_history}")
        # print("Conversation_HIstory length",len(conversation_history))
        if inference_payload.creative:
            intent_data = determine_intent(user_query=inference_payload.query, conversation_history=conversation_history, prompt_file="intention", creative_provided=True)
        else:
            intent_data = determine_intent(user_query=inference_payload.query, conversation_history=conversation_history, prompt_file="intention", creative_provided=False)
        required_outcomes = intent_data.get('required_outcomes', [11])
        unrelated_query = intent_data.get('unrelated_query', False)  
        parameters = intent_data.get('parameters', {}) 
        enhanced_query = intent_data.get('enhanced_query', inference_payload.query) 
        vector_search = intent_data.get('vector_search', False) 
        # enhanced_query = inference_payload.query
        # if vector_search:
        #     print("generatin enhanced query")
        # enhanced_query = await enhance_query(inference_payload.query,conversation_history)

        print("INTENT OUTPUT:",intent_data)
        # print("Intent Extracted:\n", "Query:",enhanced_query,"\nRequired Outcomes",required_outcomes,"\nvector_search:",vector_search)
        if unrelated_query:
            conversation_history = ""

        # Irrelevant Questions
        if 11 in required_outcomes:
            yield {"response": "I specialize in media marketing campaigns plan generation and historical data insights. Is there anything related to media campaigns that I can assist you with?\n"}
            return
        # Follow up Questions
        if 9 in required_outcomes:
            follow_up_message = intent_data.get('follow_up', 'Could you explain your query further') 
            yield {"response":follow_up_message}
        # Creative Feedback - Constructive Feedback based on provided Creative
        if 8 in required_outcomes:
            result = ideate_to_create_without_rag(inference_payload.query, inference_payload.creative, conversation_history)
            result = replace_hash_with_url(remove_markdown_prefix(result))
            yield {"response": result}        
        # Creative Trends analysis 
        if 6 in required_outcomes:
            result = ideate_to_create_with_rag(
                user_query=inference_payload.query,
                creative=inference_payload.creative,
                conversation_history=conversation_history,
                parameters=parameters
            )
            result = replace_hash_with_url(remove_markdown_prefix(result))
            yield {"response": result}
            return 
        # Generic queries 

        if 10 in required_outcomes:
            if inference_payload.creative:
                if vector_search:
                    filtered_data  = search_qdrant(enhanced_query, conversation_history, parameters, use_vector_search=True, number_of_results= threshold)
                    result = generic_with_creative(user_query=inference_payload.query, creative=inference_payload.creative,conversation_history= conversation_history,filtered_data=filtered_data)
                    result = replace_hash_with_url(remove_markdown_prefix(result))
                    yield {"response": result}
                else:
                    result = generic_with_creative(user_query=inference_payload.query, creative=inference_payload.creative, conversation_history=conversation_history)
                    result = replace_hash_with_url(remove_markdown_prefix(result))
                    yield {"response": result}
            else:
                if vector_search:
                    filtered_data  = search_qdrant(enhanced_query, conversation_history, parameters, use_vector_search=True, number_of_results= threshold)
                    result = await generic_without_creative(inference_payload.query, conversation_history,filtered_data=filtered_data)
                    yield {"response": f"{result}\n\n"}
                else:
                    result = await generic_without_creative(inference_payload.query, conversation_history)
                    yield {"response": f"{result}\n\n"}

        if any(num in required_outcomes for num in [1, 2, 3, 4, 5]):
            filtered_data = search_qdrant(enhanced_query, conversation_history, parameters, False, 10)          
            # print(f"Original data:{filtered_data}")
            
            if not filtered_data.results:
                yield {"response":"Searching for data most related with your query...\n"}
<<<<<<< HEAD
                filtered_data = search_qdrant(enhanced_query, conversation_history, parameters, use_vector_search=True, number_of_results= threshold)
                # print("Additional_Data Data1:",filtered_data)
=======
                filtered_data = search_qdrant(inference_payload.query, conversation_history, parameters, use_vector_search=True, number_of_results= threshold)
>>>>>>> 690f1ed (Quick Changes - Negative messages removed, Budget Added)
                if len(filtered_data.results)<1:
                    yield {"response":"Media Campaign Information related to your query were not found. Please try a different query.\n"}
                    return

            elif len(filtered_data.results) < threshold:
                # yield {"response":"Found and filtered some relevant data. Searching for additional data most relevant to your query...\n"}

                currently_present_ids = [i.id for i in filtered_data.results]
                additional_data = search_qdrant(enhanced_query, conversation_history, parameters, use_vector_search=True, number_of_results=(threshold - len(filtered_data.results)))
                # print("Additional_Data 2:",additional_data)
                if len(additional_data.results)>0:
                    # yield {"response":"Incorporating additional data to your response.\n"}
                    for additional_result in additional_data.results:
                        if additional_result.id not in currently_present_ids:
                            filtered_data.results.append(additional_result)
                            filtered_data.total += 1
            output_parts = OrderedDict()
            ordered_keys = ["media_plan", "analysis_of_trends", "campaign_performance", "creative_insights", "performance_summary"]

            for outcome in required_outcomes:
                if outcome == 1:  # Specifically call media_plan
                    async for chunk in media_plan(filtered_data, enhanced_query, conversation_history):
                        yield {"response": chunk}
                elif outcome in [2,3,4]:
                    insight_function = await get_insight_function(outcome)
                #  logger.debug(f"Insight function:{insight_function}  Filtred data:{filtered_data}")
                    result = await insight_function(filtered_data, enhanced_query, conversation_history)
                #  logger.debug(f"Before:{result}")
                    result = replace_hash_with_url(remove_markdown_prefix(result))
                    # print("After",result)
                    output_parts[ordered_keys[outcome - 1]] = result
                #  logger.debug(f"Completed outcome {outcome}: {result}")
                    yield {"response": result}  # Stream response
            # Process performance_summary if needed
            if 5 in required_outcomes:
                performance_summary_result = await performance_summary(enhanced_query, output_parts)
                performance_summary_result = replace_hash_with_url(remove_markdown_prefix(performance_summary_result))
                output_parts["performance_summary"] = performance_summary_result
                yield {"response": f"{performance_summary_result}\n\n"}
                # Creative Inspiration - generate images or creatives 

        if 7 in required_outcomes:
            if inference_payload.creative:
                result = await creative_inspiration_with_generation(enhanced_query=enhanced_query, creative=inference_payload.creative, conversation_history=conversation_history,vector_search=vector_search)
            else:
                result = await creative_inspiration_with_generation(enhanced_query=enhanced_query,conversation_history= conversation_history, vector_search=vector_search)
            # result = replace_hash_with_url(remove_markdown_prefix(result))
            # print("returning image:",result)
            yield {"response": result}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        yield {"response": f"An error occurred: {e}\n"}

# @timer_decorator 
async def get_insight_function(outcome):
    """ Maps required outcomes to their corresponding async functions. """
    mapping = {
        1: media_plan,          
        2: analysis_of_trends, 
        3: campaign_performance,
        4: creative_insights,
    }
    return mapping.get(outcome)
