from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue
from typing import Dict, Any, List
from openai import OpenAI
from model import AdCreative, SearchResult, InferencePayload, ConversationPayload, IntentOutput, MediaPlanOutput, AnalysisOfTrends,CreativeInsightsReport,PerformanceSummary # MediaPlanSearchResult, MediaPlanCreative, CampaignPerformanceReport
import os
import re
from dotenv import load_dotenv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List,Generator, Type, Dict, Any, Optional
from pydantic import BaseModel
import time
import asyncio


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
    
# def search_qdrant(parameters: Dict[str, Any], query_text: str, conversation_payload: list) -> SearchResult:
@timer_decorator 
def search_qdrant( query_text: str, conversation_payload: list) -> SearchResult:
    # Needs to be improved - Issues with filtering.
    formatted_history = format_conversation_payload(conversation_payload)
    enriched_query_text = f"{formatted_history}\nUser Query: {query_text}"
    
    query_vector = get_embedding(enriched_query_text)
    if not query_vector:
        print("No query vector obtained from the text.")
        return SearchResult(results=[], total=0)

    filter_conditions = []
    numeric_fields = ["file_size", "booked_measure_impressions", "delivered_measure_impressions", "clicks", "conversion", "duration"]
    text_fields = ["file_type", "industry", "targeting", "duration_category", "brand", "season_holiday"]

    # def normalize_text(value: str) -> str:
    #     return value.lower()

    # for key, value in parameters.items():
    #     try:
    #         if key in numeric_fields:
    #             filter_conditions.append(
    #                 FieldCondition(key=key, range=Range(gte=float(value)))
    #             )
    #             print(f"Added numeric filter for {key}: {value}")
    #         elif key in text_fields:
    #             normalized_value = normalize_text(value)
    #             filter_conditions.append(
    #                 FieldCondition(key=key, match=MatchValue(value=normalized_value))
    #             )
    #             print(f"Added text filter for {key}: {normalized_value}")
    #         elif key == 'perform_well' and value:
    #             filter_conditions.append(
    #                 FieldCondition(key="conversion", range=Range(gte=0.01))  # Adjust value as needed
    #             )
    #             print(f"Added performance filter based on conversion: {value}")
    #     except ValueError as e:
    #         print(f"Error processing parameter {key}: {e}")

    # print("Filter Conditions:", filter_conditions)

    # search_filter = Filter(should=filter_conditions) if filter_conditions else None

    # print("Search Filter Conditions:", search_filter)
    try:
        search_result = Qclient.search(
            collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
            query_vector=query_vector,
            # query_filter=search_filter,
            limit=10  # Increase the limit to ensure we have enough results to process
        )
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        return SearchResult(results=[], total=0)

    # if not search_result:
    #     print("No results found with filters. Falling back to vector search.")
    #     try:
    #         search_result = Qclient.search(
    #             collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
    #             query_vector=query_vector,
    #             limit=10,
    #         )
    #         print("Fallback search completed.")
    #     except Exception as e:
            # print(f"Error in fallback search: {e}")
            # return SearchResult(results=[], total=0)

    # print(f"Total results obtained: {len(search_result)}")

    # Track IDs of initial results to avoid duplicates
    initial_result_ids = {hit.id for hit in search_result}

    # Process results and score them
    results_with_scores = []
    for hit in search_result:
        payload = hit.payload
        score = hit.score
        if 'full_data' in payload and isinstance(payload['full_data'], str):
            try:
                payload['full_data'] = json.loads(payload['full_data'])
            except json.JSONDecodeError:
                payload['full_data'] = None

        try:
            ad_creative = AdCreative(**payload)
            results_with_scores.append((ad_creative, score))
            # print(f"Processed result with score {score}: {payload.get('campaign_folder')}")
        except ValueError as e:
            print(f"Error processing media creative: {e}")

    # print(f"Number of results after relevance filtering: {len(results_with_scores)}")

    # Enforce campaign folder limits
    campaign_count = {}
    limited_results = []
    relevance_threshold = 0.50

    for ad_creative, score in results_with_scores:
        campaign_folder = ad_creative.campaign_folder
        
        if campaign_folder in campaign_count:
            if campaign_count[campaign_folder] < 3:
                limited_results.append(ad_creative)
                campaign_count[campaign_folder] += 1
        else:
            limited_results.append(ad_creative)
            campaign_count[campaign_folder] = 1

    # print(f"Number of results after campaign folder limit: {len(limited_results)}")

    # Ensure at least 5 results
    if len(limited_results) < 4:
        print("Less than 5 results found with relevance threshold. Performing additional search.")
        try:
            additional_results = Qclient.search(
                collection_name="Media_Performance",
                query_vector=query_vector,
                limit=40  # Adjust the limit based on your requirements
            )
            print("Additional search completed.")

            # Filter out results already included in initial results
            additional_results = [hit for hit in additional_results if hit.id not in initial_result_ids]
            results_with_scores = []
            for hit in additional_results:
                payload = hit.payload
                score = hit.score
                if 'full_data' in payload and isinstance(payload['full_data'], str):
                    try:
                        payload['full_data'] = json.loads(payload['full_data'])
                    except json.JSONDecodeError:
                        payload['full_data'] = None

                try:
                    ad_creative = AdCreative(**payload)
                    results_with_scores.append((ad_creative, score))
                    print(f"Processed additional result with score {score}: {ad_creative.campaign_folder}")
                except ValueError as e:
                    print(f"Error processing additional media creative: {e}")

            # Reapply relevance filtering
            additional_relevant_results = [result for result, score in results_with_scores if score >= relevance_threshold]
            # print(f"Number of additional results after relevance filtering: {len(additional_relevant_results)}")

            # Combine and enforce campaign folder limits
            combined_results = limited_results + additional_relevant_results
            campaign_count = {}
            final_results = []
            for ad_creative in combined_results:
                campaign_folder = ad_creative.campaign_folder
                if campaign_folder in campaign_count:
                    if campaign_count[campaign_folder] < 3:
                        final_results.append(ad_creative)
                        campaign_count[campaign_folder] += 1
                else:
                    final_results.append(ad_creative)
                    campaign_count[campaign_folder] = 1

            print(f"Number of final results before limit: {len(final_results)}")
            
            # Limit to a maximum of 6 results
            final_results = final_results[:4]
            print(f"Number of final results after enforcing max limit: {len(final_results)}")

            if not final_results:
                return SearchResult(results=[], total=0)

            return SearchResult(results=final_results, total=len(final_results))
        except Exception as e:
            print(f"Error in additional search: {e}")
            return SearchResult(results=[], total=0)

    # Final results already limited to 6
    limited_results = limited_results[:4]
    # print("Limited Results:",limited_results[:2])
    return SearchResult(results=limited_results, total=len(limited_results))
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
            response_format=IntentOutput,
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
async def formatter(final_output: str = None, prompt_file_name: str = "formatter") -> str:
    system_prompt = load_prompt(prompt_file_name)
    query = f"Content to be formatted: {final_output}"
    formatted_output = await generate_response(
        query=query,
        system_prompt=system_prompt,
        max_tokens=4000
    )
    return formatted_output
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
    # print("Media_plan outputlen:",len(raw_response))
    return await formatter(raw_response,"formatter_media_plan")

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
        "imagery"
    ]
    full_data_fields_to_extract = [
        "product/service",
    ]
    
    essential_data = extract_specific_fields(filtered_data, fields_to_extract, full_data_fields_to_extract)

    system_prompt = load_prompt("campaign_performance_with_formatter")

    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        # response_class=CampaignPerformanceReport,
        max_tokens=4000
    )
    # return await formatter(raw_response, "formatter_campaign_performance")
    
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
    
    # print("Analysis of trends len:", len(raw_response))

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
        "imagery"
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
    
    # print("creative insight Input len:", len(query) + len(system_prompt) + len(essential_data) + len(conversation_history))
    
    # Use the async version of generate_response
    raw_response = await generate_response(
        query=query,
        system_prompt=system_prompt,
        search_result=essential_data,
        conversation_history=conversation_history,
        response_class=CreativeInsightsReport
    )
    # print("Creative Insights len:", len(raw_response))
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
    md5_pattern_thumbnail = r'\b([a-fA-F0-9]{32})\.thumbnail\.jpg\b'
    md5_pattern_data = r'data-md5-hash="([a-fA-F0-9]{32})"'
    openMediaModal_pattern = r"openMediaModal\('([a-fA-F0-9]{32})'"

    def replace_thumbnail(match):
        hash_value = match.group(1)
        return get_url_for_hash(hash_value, "thumbnail.jpg")
    
    def replace_data(match):
        hash_value = match.group(1)
        file_extension = get_extension_for_hash(hash_value)
        return get_url_for_hash(hash_value, file_extension)

    def replace_openMediaModal(match):
        hash_value = match.group(1)
        file_extension = get_extension_for_hash(hash_value)
        return f"openMediaModal('{get_url_for_hash(hash_value, file_extension)}'"
    
    # Replace thumbnail URLs
    S = re.sub(md5_pattern_thumbnail, replace_thumbnail, S)
    
    # Replace display none hashes
    S = re.sub(md5_pattern_data, replace_data, S)
    
    # Replace openMediaModal hashes
    S = re.sub(openMediaModal_pattern, replace_openMediaModal, S)
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

@timer_decorator 
def remove_html_prefix(s):
    s = re.sub(r'```html', '', s)
    s = re.sub(r'```', '<br>', s)
    s = re.sub(r'### (.*)\n', r'<h2><strong>\1</strong></h2><br>\n', s)
    s = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', s)
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
        if conversation_history:
            print("response : Received conversation payload\n")
        intent_data = determine_intent(inference_payload.query, conversation_history)
        if not intent_data:
            print("Retrying Intent\n")
            intent_data = determine_intent(inference_payload.query, conversation_history)
        required_outcomes = intent_data.get('required_outcomes')
        if 0 in required_outcomes:
            yield {"response": "I am unable to provide a response to your query.\n"}
            return

        filtered_data = search_qdrant(inference_payload.query, conversation_history)
        if not filtered_data.results:
            yield {"response": "I couldn't find any relevant information based on your query. Could you please rephrase or provide more details?\n"}
            return

        output_parts = {}
        ordered_keys = ["media_plan", "analysis_of_trends", "campaign_performance", "creative_insights", "performance_summary"]
        
        async def process_insight(outcome):
            insight_function = await get_insight_function(outcome)
            result = await insight_function(filtered_data, inference_payload.query, conversation_history)
            return outcome, replace_hash_with_url(remove_html_prefix(result))

        # Process Media_plan first if it's in required_outcomes
        if 1 in required_outcomes:
            media_plan_result = await process_insight(1)
            full_media_plan = media_plan_result[1]
            import re
            parts = re.split(r'<h2\s+class="h2">\s*Target Audience\s*</h2>', full_media_plan, 1)
            
            if len(parts) > 1:
                executive_summary = parts[0].strip()
                rest_of_media_plan = f'<h2 class="h2">Target Audience</h2>{parts[1]}'
                output_parts[ordered_keys[0]] = full_media_plan
                # Send only the Executive Summary
                print(f"Sending Executive Summary for {ordered_keys[0]}")
                yield {"response": executive_summary}
                await asyncio.sleep(0.1)
                # Send the rest of the media plan separately
                print(f"Sending rest of Media Plan for {ordered_keys[0]}")
                yield {"response": rest_of_media_plan}
            else:
                # If "Target Audience" is not found, send the entire media plan
                print(f"Sending full Media Plan for {ordered_keys[0]}")
                yield {"response": full_media_plan}

        # Process other insights
        other_tasks = [
            process_insight(outcome)
            for outcome in required_outcomes if outcome in [2, 3, 4]
        ]

        if other_tasks:
            print("Processing other insights.")
            other_results = await asyncio.gather(*other_tasks)
            
            for outcome, result in other_results:
                output_parts[ordered_keys[outcome-1]] = result
                print(f"Sending response for {ordered_keys[outcome-1]}: {result}")
                yield {"response": result}

        # Call performance_summary with the gathered insights if needed
        if 5 in required_outcomes:
            performance_summary_result = await performance_summary(inference_payload.query, output_parts)
            performance_summary_result = replace_hash_with_url(remove_html_prefix(performance_summary_result))
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
        3: creative_insights,
        4: campaign_performance,
        5: performance_summary,
    }
    return mapping.get(outcome)


