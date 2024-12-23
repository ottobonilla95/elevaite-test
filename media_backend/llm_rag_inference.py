from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue, MatchAny
from fastapi import HTTPException
from typing import Dict, Any, List
from openai import OpenAI
from model import MessageData, AdCreative, SearchResult, InferencePayload, ConversationPayload, IntentOutput, MediaPlanOutput, AnalysisOfTrends,CreativeInsightsReport,PerformanceSummary ,AnalysisOfTrendsTwo,AnalysisOfTrendsOne,AnalysisOfTrendsThree# MediaPlanSearchResult, MediaPlanCreative, CampaignPerformanceReport
import os
import re
import ast
from dotenv import load_dotenv
from io import BytesIO
import json
from typing import List, Type, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel
import time
import requests
import asyncio
from prompts.prompts import SystemPrompts
from sentence_transformers import CrossEncoder
from collections import OrderedDict
from cache_control import CacheControl

import logging
# Timer and logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# cache_control = CacheControl()

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2",tokenizer_args={'clean_up_tokenization_spaces': True})

def timer_decorator(func):
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        # logger.info(f"{func.__name__} started at {start:.6f} seconds")
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        # logger.info(f"{func.__name__} ended at {end:.6f} seconds")
        logger.info(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        # logger.info(f"{func.__name__} started at {start:.6f} seconds")
        result = func(*args, **kwargs)
        end = time.perf_counter()
        # logger.info(f"{func.__name__} ended at {end:.6f} seconds")
        logger.info(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
    
def load_prompt(prompt_name):
    """
    Fetches the prompt by name from the SystemPrompts class.
    Args:
        prompt_name (str): The name of the prompt to retrieve.
    Returns:
        str: The prompt text, or an error message if not found.
    """
    return SystemPrompts.get_prompt(prompt_name)

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
    
def rerank_results(query_text: str, results: List[AdCreative], enriched_query_text: str) -> List[AdCreative]:
    """Rerank results based on query relevance, considering dynamic contextual terms from the enriched query."""    
    # Process the enriched query to detect key contextual terms (e.g., industries, product categories, etc.)
    # This should capture the terms from the enriched query dynamically without hardcoding
    enriched_query_terms = set(enriched_query_text.lower().split())
    reranker_input = []
    for ad_creative in results:
        brand = ad_creative.brand or ""
        business_category = ad_creative.industry or ""  # Assuming business_category is stored in 'industry'
        # Concatenate the enriched query with brand and business_category for better contextual matching
        reranker_input.append((enriched_query_text, f"{brand} {business_category}"))
    
    scores = reranker.predict(reranker_input)    
    reranked_results = []

    for ad_creative, score in zip(results, scores):
        # Check if any of the enriched query terms match the brand or business category
        industry_terms = set(ad_creative.industry.lower().split()) if ad_creative.industry else set()
        brand_terms = set(ad_creative.brand.lower().split()) if ad_creative.brand else set()
        # Check for overlap between the enriched query terms and the ad's brand/industry terms
        relevance_bonus = len(enriched_query_terms.intersection(industry_terms.union(brand_terms)))
        # Combine the Cross-Encoder score with the relevance bonus
        final_score = score + relevance_bonus
        reranked_results.append((ad_creative, final_score))
    # Sort by final score (higher is better)
    reranked_results = sorted(reranked_results, key=lambda x: x[1], reverse=True)
    print("Re-ranked Scores:", [score for _, score in reranked_results])
    return [result[0] for result in reranked_results]

def get_past_vectors_for_topic(existing_data: List[dict], current_topic: str) -> List[dict]:
    """
    Retrieves vector data from past sessions that match the current topic.
    Args:
        existing_data (List[dict]): The past session data containing topics and vector data.
        current_topic (str): The current topic to match against past session topics.

    Returns:
        List[dict]: A list of vector data associated with similar campaigns in the past.
    """
    past_vectors = []
    for session in existing_data:
        if 'topic' in session and session['topic'] == current_topic:
            if 'vector_data' in session:
                past_vectors.extend(session['vector_data'])
    return past_vectors

def check_non_empty_fields_for_topic(existing_data: List[dict], current_topic: str) -> List[str]:
    """
    Checks which fields have non-empty strings for the given topic in past session data.
    
    Args:
        existing_data (List[dict]): The past session data containing topics and fields to check.
        current_topic (str): The current topic to match against past session topics.
        
    Returns:
        List[str]: A list of field names that have non-empty strings for the given topic.
    """
    fields_to_check = ['media_plan_output', 'campaign_performance_output', 'creative_insights_output']
    non_empty_fields = []

    for session in existing_data:
        if session.get('topic') == current_topic:
            for field in fields_to_check:
                if field in session and isinstance(session[field], str) and session[field].strip():
                    non_empty_fields.append(field)

    return list(set(non_empty_fields))

@timer_decorator
async def topic_extractor(past_topics: List[str], enhanced_query: str) -> str:
    """
    Extracts the topic from the user's session history and compares it with the current enhanced query using an LLM.

    Args:
        past_topics (List[str]): A list of topics from the user's previous session history.
        enhanced_query (str): The current enhanced query from the user.

    Returns:
        str: The current topic determined by the LLM.
    """
    # Prepare the prompt for the LLM
    prompt = load_prompt("topic_extractor").format(", ".join(past_topics), enhanced_query)
    try:
        # Use the existing generate_response function to get the topic
        response_content = await generate_response(
            query=prompt,
            system_prompt="You are an AI that determines topics based on user queries.",
            max_tokens=150,
        )
        # Return the response content as the current topic
        return response_content
    except Exception as e:
        logger.error(f"Error in topic extraction: {e}")
        return ""

# Searches Qdrant and returns search result object
def search_qdrant(query_text: str, conversation_payload: list, parameters: Dict[str, Any], use_vector_search: bool = False, number_of_results: int = 4) -> SearchResult:
    formatted_history = format_conversation_payload(conversation_payload)
    enriched_query_text = f"{formatted_history}\nUser Query: {query_text}"
    # print("Query Used for Vector Search:",enriched_query_text)
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
                limit=number_of_results*10,
            )
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return SearchResult(results=[], total=0)

        # Process vector search results
        # print("SEARCH RESULTS:",search_result)
        for hit in search_result:
            # if hit.score > 0.70: # Magic number
            try:
                    # print("Vector search score:", hit.score)
                ad_creative = AdCreative.parse_obj(hit.payload)
                brand_name = ad_creative.brand
                if brand_name not in brand_count:
                    brand_count[brand_name] = 0
                if brand_count[brand_name] < 1:  # Limit to 2 per brand
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
                    limit=number_of_results*10,
                )
            except Exception as e:
                logger.error(f"Error searching Qdrant: {e}")
                return SearchResult(results=[], total=0)
            
            # Process filtered search results with brand limit
            brand_count = {}
            for index, hit in enumerate(search_result):
                # if hit.score>0.70: # Magic Number
                try:
                    # print("Filtered score:",hit.score)
                    payload = hit.payload
                    ad_creative = AdCreative.parse_obj(payload)
                    brand_name = ad_creative.brand
                    if brand_name not in brand_count:
                        brand_count[brand_name] = 0
                    if brand_count[brand_name] < 1:  # Limit to 2 per brand
                        ad_creatives.append(ad_creative)
                        brand_count[brand_name] += 1
                    else:
                        logger.info(f"Skipped AdCreative for brand: {brand_name}")
                except ValueError as e:
                    logger.error(f"Error processing media creative {index + 1}: {e}")
                    logger.error(f"Problematic payload: {payload}")
    if ad_creatives:
        ad_creatives = rerank_results(query_text, ad_creatives,enriched_query_text)
    else:
        logger.warning("No valid results found after filtering and validation.")
        return SearchResult(results=[], total=0)

    final_results = ad_creatives[:number_of_results]
    logger.info(f"Final Results: {len(final_results)}")
    return SearchResult(results=final_results, total=len(final_results))

# Identifies the intent and enhances the query
@timer_decorator   
def determine_intent(user_query: str, conversation_history: List[ConversationPayload],prompt_file: str,creative_provided: bool = False) -> dict:
    try:

        system_prompt = load_prompt(prompt_file)
        if creative_provided:
            system_prompt += "creative provided: true\n"
        else:
            system_prompt += "creative provided: false\n"

        messages = [{"role": "system", "content": system_prompt}]
        for message in conversation_history:
            messages.append({"role": message.actor, "content": message.content})
        
        messages.append({"role": "user", "content": user_query})
        
        print("Input to the intent:",messages)
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            response_format=IntentOutput,
            max_tokens=500
        )
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
            "model": "gpt-4o",
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
            if content:
                yield content
    except Exception as e:
        logger.error(f"Error in generating response: {e}")
        yield f"Error: {str(e)}"


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
            "model": "gpt-4o",
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
            "model": "gpt-4o",
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
            "model": "gpt-4o",
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
    max_prompt_length = 2048  # Set to 2048 as per the API documentation
    if len(prompt) > max_prompt_length:
        prompt = prompt[:max_prompt_length] 
        
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

def generate_image_url(md5_hash):
    """Generate the image URL from the given MD5 hash."""
    base_url = os.getenv("BASE_URL_FOR_CREATIVES")
    return f"{base_url}{md5_hash[:2]}/{md5_hash[2:4]}/{md5_hash}.thumbnail.jpg"

def formatter_for_creative_insight(data):
    """Convert JSON input to a Markdown formatted string."""
    markdown_output = "## Creative Insights\n\n"
    for creative in data["creatives"]:
        brand = creative["brand"]
        product = creative["product"]
        snapshot = creative["creative_snapshot"]
        elements = creative["creative_elements"]

        # Extract and parse the MD5 hash for the image URL
        thumbnail, md5_hash = map(str.strip, elements["creative_thumbnail"].split(","))
        # image_url = generate_image_url(md5_hash)

        markdown_output += f"\n### Brand: {brand}, Product: {product}\n\n"
        markdown_output += f"![{thumbnail}]({md5_hash} \"{product}\")\n\n"
        markdown_output += f"| **Creative Snapshot** | {snapshot} |\n"
        markdown_output += f"|-----------------------|-----------------------------------------------------------------------------------------------------|\n"
        markdown_output += f"| **Brand Elements**    | {elements['brand_elements']} |\n"
        markdown_output += f"| **Visual Elements**   | {elements['visual_elements']} |\n"
        markdown_output += f"| **Color Tone**        | {elements['color_tone']} |\n"

        optional_elements = ["cinematography", "audio_elements", "narrative_structure", "seasonal_holiday_elements"]
        for opt_elem in optional_elements:
            if elements.get(opt_elem):  # Check if the key exists and is not empty
                formatted_key = opt_elem.replace("_", " ").capitalize()
                markdown_output += f"| **{formatted_key}**    | {elements[opt_elem]} |\n"

        markdown_output += "\n"

    return markdown_output


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
async def media_plan(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload], past_vector_names: Optional[List[str]] = None) ->  AsyncGenerator[str, None]:
    # Media_plan Data filtered out
    fields_to_extract = [
    "ad_objective",
    "brand",
    "industry",
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
    print(f"Essential data:{essential_data}")
    system_prompt = load_prompt("media_plan")

    if past_vector_names:
        system_prompt += f"\nPrioritize past vectors that were used for the previous queries which are listed as follows:{', '.join(past_vector_names)}"
    # print("Prompt used for media plan:",system_prompt)
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
    # print(f"Media_plan Raw text:{raw_response}")
    async for chunk in formatter_streaming(raw_response, "formatter_media_plan", query):
            yield chunk
    # return await formatter(raw_response,"formatter_media_plan",query)

@timer_decorator
async def campaign_performance(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload], past_vector_names: Optional[List[str]] = None
) -> str:
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
    if past_vector_names:
        system_prompt += f"\nPrioritize past vectors that were used for the previous queries which are listed as follows:{', '.join(past_vector_names)}"
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
    # print(f"Campaign Performance Raw text:{raw_response}")
    return raw_response

@timer_decorator
async def analysis_of_trends(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload], past_vector_names: Optional[List[str]] = None) -> str:
    tasks = [
        perform_analysis(filtered_data, query, conversation_history, "analysis_of_trends_one", AnalysisOfTrendsOne, "formatter_analysis_of_trends_first",past_vector_names),
        perform_analysis(filtered_data, query, conversation_history, "analysis_of_trends_two", AnalysisOfTrendsTwo, "formatter_analysis_of_trends_other",past_vector_names),
        perform_analysis(filtered_data, query, conversation_history, "analysis_of_trends_three", AnalysisOfTrendsThree, "formatter_analysis_of_trends_other",past_vector_names)
    ]
    raw_responses = await asyncio.gather(*tasks)
    return "\n".join(raw_responses)

@timer_decorator
async def perform_analysis(
    filtered_data: SearchResult,
    query: str,
    conversation_history: List[ConversationPayload],
    prompt_name: str,
    response_class: type,
    formatter_name: str,
    past_vector_names: Optional[List[str]] = None
) -> str:
    fields_to_extract = [
        "brand", "industry", "ad_objective", "tone_mood", "duration(days)", "duration_category",
        "targeting", "booked_measure_impressions", "conversion", "file_type", "type"
    ]
    full_data_fields_to_extract = [
        "call-to-action", "strategy", "weekends", "holidays", "national events",
        "sport events", "visual elements", "imagery"
    ]
    # Extract relevant data
    essential_data = extract_specific_fields(filtered_data, fields_to_extract, full_data_fields_to_extract)
    # Load prompt
    system_prompt = load_prompt(prompt_name)
    if past_vector_names:
        system_prompt += f"\nPrioritize past vectors that were used for the previous queries which are listed as follows:{', '.join(past_vector_names)}"

    # Generate response
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=response_class
    )
    # Format the response
    # print(f"Analysis of Trends Raw text:{raw_response}")
    return await formatter(raw_response, formatter_name)

@timer_decorator
async def creative_insights(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload], past_vector_names: Optional[List[str]] = None) -> str:
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
    if past_vector_names:
        system_prompt += f"\nPrioritize past vectors that were used for the previous queries which are listed as follows:{', '.join(past_vector_names)}"
    # print("Essential data:",essential_data)
    # Use the async version of generate_response
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=CreativeInsightsReport
    )
  #  logger.debug(f"Creative Insights Raw: {raw_response}")
    # print(f"Creative insights raw_response: {raw_response}")
    formatted_response = formatter_for_creative_insight(json.loads(raw_response))
    # formatted_response = await formatter(raw_response, "formatter_creative_insights_v2")
    # print("Formatted response:",formatted_response)
    return formatted_response
    
# @timer_decorator
# async def creative_insights(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
#     # Fields to extract for creatives
#     fields_to_extract = [
#         "brand",
#         "ad_objective",
#         "tone_mood",
#         "md5_hash",
#         "colors",
#         "duration(days)",
#         "duration_category",
#         "imagery",
#         "file_name",
#     ]
#     full_data_fields_to_extract = [
#         "product/service",
#         "call-to-action",
#         "strategy",
#         "visual elements",
#         "cinematography",
#         "audio elements",
#         "narrative structure",
#         "weekends",
#         "holidays",
#         "national events",
#         "sport events",
#     ]

#     def clean_json_like_data(raw_data: str) -> str:
#         """
#         Cleans and converts a JSON-like string (with single quotes, etc.)
#         into a valid JSON string using ast.literal_eval.
#         """
#         try:
#             # Convert the raw string to a Python object
#             python_data = ast.literal_eval(raw_data)
#             # Convert the Python object back to a valid JSON string
#             cleaned_json = json.dumps(python_data)
#             return cleaned_json
#         except Exception as e:
#             raise ValueError(f"Failed to clean JSON-like data: {e}")

#     # Extract specific fields for all creatives
#     raw_essential_data = extract_specific_fields(filtered_data, fields_to_extract, full_data_fields_to_extract)
#     # print("Raw:", raw_essential_data)

#     try:
#         # Clean and validate JSON data
#         cleaned_data = clean_json_like_data(raw_essential_data)
#         essential_data_list = json.loads(cleaned_data)
#         logger.info(f"Parsed {len(essential_data_list)} creatives for processing.")
#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to parse extracted data: {e}")
#         logger.debug(f"Raw Data: {raw_essential_data}")  # Log raw data for debugging
#         return "Error parsing extracted data."
#     except Exception as e:
#         logger.error(f"Unexpected error during data parsing: {e}")
#         return "An unexpected error occurred during data parsing."

#     # Load the system prompt once
#     system_prompt = load_prompt("creative_insights_new")

#     async def process_creative(creative_data):
#         """Processes a single creative asynchronously."""
#         try:
#             # Generate response for a single creative
#             raw_response = await generate_response(
#                 query=query,
#                 system_prompt=system_prompt,
#                 search_result=json.dumps(creative_data),  # Ensure data is serialized correctly
#                 conversation_history=conversation_history,
#                 response_class=CreativeInsightsReport,
#             )
#             # Format the raw response
#             return await formatter(raw_response, "formatter_creative_insights")
#         except Exception as e:
#             logger.error(f"Error processing creative {creative_data.get('file_name', 'unknown')}: {e}")
#             return f"Error processing creative {creative_data.get('file_name', 'unknown')}"

#     # Ensure the input is not empty to avoid unnecessary calls
#     if not essential_data_list:
#         return "No valid creatives found for processing."

#     # Process all creatives concurrently using asyncio.gather
#     tasks = [process_creative(creative) for creative in essential_data_list]
#     results = await asyncio.gather(*tasks, return_exceptions=True)

#     # Combine formatted outputs into a unified Markdown response
#     markdown_output = "## Creative Insights\n\n"
#     for index, result in enumerate(results):
#         if isinstance(result, Exception):
#             logger.error(f"Task {index} failed with error: {result}")
#             markdown_output += f"### Creative {index + 1}: Error\n{result}\n\n"
#         else:
#             # Append formatted creative insights with a heading
#             markdown_output += f"### Creative {index + 1}\n{result.strip()}\n\n"

#     return markdown_output

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
# def get_extension_for_hash(hash):
#     # Use forward slashes for cross-platform compatibility
#     base_path = "static/images"  # Change to your actual path
#     extensions = ['jpg', 'mov', 'png', 'gif', 'mp4']
#     # Construct the directory structure using os.path.join
#     directory_structure = os.path.join(base_path, hash[:2], hash[2:4])
#     for ext in extensions:
#         file_path = os.path.join(directory_structure, f"{hash}.{ext}")
#         file_path = os.path.normpath(file_path)  # Normalize the path
#         # print(f"Checking: {file_path}")  # Debug line
#         if os.path.isfile(file_path):
#             return ext

#     return "unknown"  # or raise an exception if preferred

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

async def generate_related_queries(intent_data: dict, conversation_history: List[ConversationPayload],user_query:str,prompt_file:str,non_empty_fields:List[str]=None,past_vector_names:List[str]=None) -> List[str]:
    """
    Generates related queries based on the intent data and previous user queries.
    
    Args:
        intent_data (dict): The intent data containing user query information.
        conversation_history (List[ConversationPayload]): The conversation history to extract previous queries.
    
    Returns:
        List[str]: A list of related queries.
    """
    # Load the prompt for generating related queries
    if non_empty_fields and past_vector_names:
        prompt = load_prompt(prompt_file).format(str(non_empty_fields),str(past_vector_names))
    elif non_empty_fields:
        prompt = load_prompt(prompt_file).format(str(non_empty_fields),"")
    elif past_vector_names:
        prompt = load_prompt(prompt_file).format("",str(past_vector_names))
    else:
        prompt = load_prompt(prompt_file)
    
    # print("Related Queries Prompt:",prompt)
    OUTCOME_MAPPING = {
    1: "Media Plan - Can create/generate a media plan for a product",
    2: "Analysis of Trends",
    3: "Campaign Performance",
    4: "Existing Creative Insights",
    5: "Performance Summary - Summary of other outputs",
    6: "Creative Trends - if creative uploaded is true, then provide creative trends",
    7: "Creative Inspiration - generate creatives using an API.",
    8: "Creative Feedback - Constructive Feedback based on provided Creative",
    9: "Follow Up Question - Ask a follow up question. If it is for creatives, ask them if they want to generate a fresh creative or base their creative off another that performed well.",
    10: "Generic Media Chatbot Questions",
    11: "Irrelevant Questions"
}
    # Extract previous user queries from the conversation history
    previous_queries = [entry.content for entry in conversation_history if entry.actor == "user"]
    required_outcomes = intent_data.get('required_outcomes', [11])
    outcome_descriptions = [OUTCOME_MAPPING.get(outcome, "Unknown Outcome") for outcome in required_outcomes]
    # Prepare the input for the LLM call
    input_data = {
        "base_query": user_query,
        "previous_queries": str(previous_queries),
        "current_intents_chosen":str(outcome_descriptions)
    }
    # Call the LLM with the prompt and input data
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": str(input_data)}],
            max_tokens=200  # Adjust max tokens as needed
        )
        related_queries = response.choices[0].message.content.strip().split('\n')
        # print("Related Queries Output:",related_queries)
        return related_queries
    except Exception as e:
        logger.error(f"Error generating related queries: {e}")
        return []


# @timer_decorator
async def perform_inference(inference_payload: InferencePayload):
    try:
        user_id = inference_payload.user_id  # Assuming user_id is part of the payload
        session_id = inference_payload.session_id  # Assuming session_id is part of the payload
        cache_key = f"{user_id}:{session_id}"
        try:
            cache_control = CacheControl()
        except Exception as e:
            yield{"response":"Error initializing cache control. Please try again later."}
            return
        media_plan_output = ""
        creative_insights_output = ""
        campaign_performance_output = ""
        general_response_string = ""
        creative_data = []
        vector_data = []
        past_topics = []
        filtered_data = None
        related_prompt_file = "related_queries_general" # Default prompt file for related queries
        existing_data_json = cache_control.get(cache_key)
        existing_data = json.loads(existing_data_json) if existing_data_json else []

        # cached_message_data = cache_control.get(cache_key)
        # if cached_message_data:
        #     message_data = MessageData.parse_obj(cached_message_data)

        # if  cached_contexts:
        #     contexts = json.loads(cached_contexts)
        #     for context in contexts:
        #         # Need a function here to check if the context is still valid
        #         # Then based on the context, either return the cached context or search for new data.
        #         print("Hi")
        # else:
        threshold = 3
        conversation_history = inference_payload.conversation_payload or []

        logger.info(f"conversation_history:{conversation_history}")
        user_query=inference_payload.query
        # print("Conversation_HIstory length",len(conversation_history))
        if inference_payload.creative:
            intent_data = determine_intent(user_query=user_query, conversation_history=conversation_history, prompt_file="intention", creative_provided=True)
        else:
            intent_data = determine_intent(user_query=user_query, conversation_history=conversation_history, prompt_file="intention", creative_provided=False)
        
        required_outcomes = intent_data.get('required_outcomes', [11])
        unrelated_query = intent_data.get('unrelated_query', False)  
        parameters = intent_data.get('parameters', {}) 
        enhanced_query = intent_data.get('enhanced_query', user_query) 
        vector_search = intent_data.get('vector_search', False) 
        
        # Extract all of the previous the topics from the redis session data.
        if 11 not in required_outcomes:
            past_topics = [session['topic'] for session in existing_data if 'topic' in session]
            # print("Existing Data:",existing_data)
            # print("Past Topics:",past_topics)

        current_topic = await topic_extractor(past_topics,enhanced_query)
        # print("Current Topic:",current_topic)  
        non_empty_fields = check_non_empty_fields_for_topic(existing_data, current_topic)
        # print(f"Non-empty fields for topic '{current_topic}': {non_empty_fields}")
        # Edit the past_vector_names so that it doesn't get duplicated in the output.
        past_vectors = get_past_vectors_for_topic(existing_data,current_topic)
        past_vector_names = ["brand: "+vector['brand']+" industry: "+vector['industry'] for vector in past_vectors]
        past_vector_names = list(set(past_vector_names))
        # logger.info("Current Topic:",current_topic)   
        
        # if past_vector_names:
            # print("Past Vectors used:",past_vector_names)
        logger.info("Intent Agent Output:",intent_data)
        print("Intent Extracted:\n", "Query:",enhanced_query,"\nRequired Outcomes",required_outcomes,"\nvector_search:",vector_search)
        print(intent_data)
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
            general_response_string += follow_up_message
        # Creative Feedback - Constructive Feedback based on provided Creative
        if 8 in required_outcomes:
            result = ideate_to_create_without_rag(user_query, inference_payload.creative, conversation_history)
            result = replace_hash_with_url(remove_markdown_prefix(result))
            yield {"response": result}      
            general_response_string += result
            related_prompt_fle = "related_queries_general"
                                
        # Uploaded Creative Trends analysis 
        if 6 in required_outcomes:
            result = ideate_to_create_with_rag(
                user_query=user_query,
                creative=inference_payload.creative,
                conversation_history=conversation_history,
                parameters=parameters
            )
            result = replace_hash_with_url(remove_markdown_prefix(result))
            yield {"response": result}
            general_response_string += result
            related_prompt_fle = "related_queries_ideate_to_create_with_rag"
        # Generic queries 

        if 10 in required_outcomes:
            if inference_payload.creative:
                if vector_search:
                    filtered_data  = search_qdrant(enhanced_query, conversation_history, parameters, use_vector_search=True, number_of_results= threshold)
                    result = generic_with_creative(user_query=user_query, creative=inference_payload.creative,conversation_history= conversation_history,filtered_data=filtered_data)
                    result = replace_hash_with_url(remove_markdown_prefix(result))
                    yield {"response": result} 
                    
                else:
                    result = generic_with_creative(user_query=user_query, creative=inference_payload.creative, conversation_history=conversation_history)
                    result = replace_hash_with_url(remove_markdown_prefix(result))
                    yield {"response": result}
            else:
                if vector_search:
                    filtered_data  = search_qdrant(enhanced_query, conversation_history, parameters, use_vector_search=True, number_of_results= threshold)
                    result = await generic_without_creative(user_query, conversation_history,filtered_data=filtered_data)
                    yield {"response": f"{result}\n\n"}
                else:
                    result = await generic_without_creative(user_query, conversation_history)
                    yield {"response": f"{result}\n\n"}
            general_response_string += result
                    
            related_prompt_fle = "related_queries_general"
            related_queries = await generate_related_queries(intent_data,conversation_history,user_query,prompt_file=related_prompt_fle)
            yield {"related_queries": related_queries}


        if any(num in required_outcomes for num in [1, 2, 3, 4, 5]):
            filtered_data = search_qdrant(enhanced_query, conversation_history, parameters, False, 10)          
            # print(f"Original data:{filtered_data}")
            
            if not filtered_data.results:
                # yield {"response":"Searching for data most related with your query...\n"}
                filtered_data = search_qdrant(enhanced_query, conversation_history, parameters, use_vector_search=True, number_of_results= threshold)
                # print("Additional_Data Data1:",filtered_data)
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


            
            vector_data = {ad_creative.id: ad_creative.dict() for ad_creative in filtered_data.results}  # Use a dictionary to avoid duplicates

            for past_vector in past_vectors:
                vector_data[past_vector['id']] = past_vector  # Assuming past_vector has an 'id' field
            # Convert back to a list
            vector_data = list(vector_data.values())
            filtered_data_with_past_vectors = SearchResult(results=[AdCreative(**data) for data in vector_data], total=len(vector_data))
            output_parts = OrderedDict()
            ordered_keys = ["media_plan", "analysis_of_trends", "campaign_performance", "creative_insights", "performance_summary"]

            for outcome in required_outcomes:
                if outcome == 1:  # Specifically call media_plan
                    async for chunk in media_plan(filtered_data_with_past_vectors, enhanced_query, conversation_history,past_vector_names):
                        if chunk:
                            yield {"response": chunk}
                            media_plan_output += chunk
                    # related_queries = await generate_related_queries(intent_data,conversation_history,user_query)
                    # # print("Related Queries:",related_queries)
                    # yield {"related_queries": related_queries}

                elif outcome in [2,3,4]:
                    insight_function = await get_insight_function(outcome)
                #  logger.debug(f"Insight function:{insight_function}  Filtred data:{filtered_data}")
                    result = await insight_function(filtered_data_with_past_vectors, enhanced_query, conversation_history)
                #  logger.debug(f"Before:{result}")
                    result = replace_hash_with_url(remove_markdown_prefix(result))
                    if outcome == 2:
                        general_response_string += result
                    elif outcome == 3:
                        campaign_performance_output += result
                    elif outcome == 4:
                        creative_insights_output += result
                    # print("After",result)
                    output_parts[ordered_keys[outcome - 1]] = result
                #  logger.debug(f"Completed outcome {outcome}: {result}")
                    yield {"response": result}  # Stream response
                    # related_queries = await generate_related_queries(intent_data,conversation_history,user_query)
                    # yield {"related_queries": related_queries}

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
            if result:
                yield {"response": result}
                creative_data.append(result)
                related_prompt_file = "related_queries_generate_advertisement"


        if 1 in required_outcomes:
            related_prompt_file = "related_queries_media_plan_v2"
        elif 2 in required_outcomes:
            related_prompt_file = "related_queries_overall_trends"
        elif 3 in required_outcomes and 4 in required_outcomes:
            related_prompt_file = "related_queries_general"
        elif 3 in required_outcomes:
            related_prompt_file = "related_queries_campaign_performance"
        elif 4 in required_outcomes:
            related_prompt_file = "related_queries_creative_insights"
        # Generate related queries only if the outcome is not 9 or 11.
        if 9 not in required_outcomes and 11 not in required_outcomes:
            if past_vector_names and non_empty_fields:
                related_queries = await generate_related_queries(intent_data,conversation_history,user_query,prompt_file=related_prompt_file, non_empty_fields=non_empty_fields, past_vector_names=past_vector_names)
            elif past_vector_names:
                related_queries = await generate_related_queries(intent_data,conversation_history,user_query,prompt_file=related_prompt_file, past_vector_names=past_vector_names)
            elif non_empty_fields:
                related_queries = await generate_related_queries(intent_data,conversation_history,user_query,prompt_file=related_prompt_file, non_empty_fields=non_empty_fields)
            else:
                related_queries = await generate_related_queries(intent_data,conversation_history,user_query,prompt_file=related_prompt_file)
            yield {"related_queries": related_queries}
        session_data = {
            "topic": current_topic,  # Extract the topic
            "message_query": user_query,
            "enhanced_query": enhanced_query,
            "vector_data": vector_data,  # Handle potential absence
            "creative_data": [],  # Placeholder for future use
            "media_plan_output": media_plan_output,
            "creative_insights_output": creative_insights_output,
            "campaign_performance_output": campaign_performance_output,
            "general_response_string": general_response_string,
        }

        existing_data.append(session_data)
        cache_control.setex(cache_key, 500, json.dumps(existing_data))  # 

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
