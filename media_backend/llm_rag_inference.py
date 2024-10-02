from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue
from typing import Dict, Any, List
from openai import OpenAI
from model import AdCreative, SearchResult, InferencePayload, ConversationPayload
import os
import re
from dotenv import load_dotenv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List,Generator


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
    
def search_qdrant(parameters: Dict[str, Any], query_text: str, conversation_payload: list) -> SearchResult:
    # Needs to be improved - Issues with filtering.
    formatted_history = format_conversation_payload(conversation_payload)
    print("Formatted historic data")
    enriched_query_text = f"{formatted_history}\nUser Query: {query_text}"
    
    query_vector = get_embedding(enriched_query_text)
    if not query_vector:
        print("No query vector obtained from the text.")
        return SearchResult(results=[], total=0)

    filter_conditions = []
    numeric_fields = ["file_size", "booked_measure_impressions", "delivered_measure_impressions", "clicks", "conversion", "duration"]
    text_fields = ["file_type", "industry", "targeting", "duration_category", "brand", "season_holiday"]

    def normalize_text(value: str) -> str:
        return value.lower()

    for key, value in parameters.items():
        try:
            if key in numeric_fields:
                filter_conditions.append(
                    FieldCondition(key=key, range=Range(gte=float(value)))
                )
                print(f"Added numeric filter for {key}: {value}")
            elif key in text_fields:
                normalized_value = normalize_text(value)
                filter_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=normalized_value))
                )
                print(f"Added text filter for {key}: {normalized_value}")
            elif key == 'perform_well' and value:
                filter_conditions.append(
                    FieldCondition(key="conversion", range=Range(gte=0.01))  # Adjust value as needed
                )
                print(f"Added performance filter based on conversion: {value}")
        except ValueError as e:
            print(f"Error processing parameter {key}: {e}")

    print("Filter Conditions:", filter_conditions)

    search_filter = Filter(should=filter_conditions) if filter_conditions else None

    print("Search Filter Conditions:", search_filter)
    try:
        search_result = Qclient.search(
            collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
            query_vector=query_vector,
            query_filter=search_filter,
            limit=10  # Increase the limit to ensure we have enough results to process
        )
        print("Initial search completed.")
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        return SearchResult(results=[], total=0)

    if not search_result:
        print("No results found with filters. Falling back to vector search.")
        try:
            search_result = Qclient.search(
                collection_name=os.getenv("COLLECTION_NAME", "Media_Performance"),
                query_vector=query_vector,
                limit=10,
            )
            print("Fallback search completed.")
        except Exception as e:
            print(f"Error in fallback search: {e}")
            return SearchResult(results=[], total=0)

    print(f"Total results obtained: {len(search_result)}")

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
            print(f"Processed result with score {score}: {payload.get('campaign_folder')}")
        except ValueError as e:
            print(f"Error processing media creative: {e}")

    print(f"Number of results after relevance filtering: {len(results_with_scores)}")

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

    print(f"Number of results after campaign folder limit: {len(limited_results)}")

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
            print(f"Number of additional results after relevance filtering: {len(additional_relevant_results)}")

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
    print("Limited Results:",limited_results[:2])
    return SearchResult(results=limited_results, total=len(limited_results))

def determine_intent(user_query: str, conversation_history: List[ConversationPayload]) -> dict:
    try:
        prompt1 = load_prompt('intent')
        messages = [{"role": "system", "content": prompt1}]
        
        for message in conversation_history:
            messages.append({"role": message.actor, "content": message.content})
        
        messages.append({"role": "user", "content": user_query})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {json_error}")
            # Return a default dictionary or handle the error as needed
            return {"error": "Failed to parse JSON response"}
    except Exception as e:
        print(f"Error determining intent: {e}")
        return {}

def format_search_results(search_result: SearchResult) -> str:
    formatted_results = []
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
    return "\n".join(formatted_results)

def generate_response(
    query: str, 
    search_result: SearchResult, 
    system_prompt: str, 
    conversation_history: List[ConversationPayload], 
    combined_output: str = None  # New optional parameter
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    
    for message in conversation_history:
        messages.append({"role": message.actor, "content": message.content})
    
    messages.append({"role": "user", "content": f"Query: {query}\n\nSearch Results: {format_search_results(search_result)}"})

    # Include combined_output if provided
    if combined_output:
        messages.append({"role": "user", "content": f"Combined Output: {combined_output}"})

    # print("Message sent:", messages)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1800,
            n=2,
            temperature=0.1,
        )
        # print("PROMPT:", system_prompt, "RESPONSE:", response.choices[0].message.content.strip())
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in generating response: {e}")
        return "I apologize, but I couldn't generate a response at this time."
    
def media_plan(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload], campaign_insights: str, creative_insights: str) -> str:
    system_prompt = load_prompt("media_plan")
    combined_output = f"{campaign_insights}\n\n{creative_insights}"
    return generate_response(query, filtered_data, system_prompt, conversation_history, combined_output)

def campaign_performance_insights(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
    system_prompt = load_prompt("campaign_performance_insights")
    return generate_response(query, filtered_data, system_prompt, conversation_history)

def creative_insights(filtered_data: SearchResult, query: str, conversation_history: List[ConversationPayload]) -> str:
    system_prompt = load_prompt("creative_insights")
    return generate_response(query, filtered_data, system_prompt, conversation_history)


def replace_hash_with_url(S):
    md5_pattern_thumbnail = r'\b([a-fA-F0-9]{32})\.thumbnail\.jpg\b'
    md5_pattern_data = r'data-md5-hash="([a-fA-F0-9]{32})"'
    
    def replace_thumbnail(match):
        hash_value = match.group(1)
        return get_url_for_hash(hash_value, "thumbnail.jpg")
    
    def replace_data(match):
        hash_value = match.group(1)
        file_extension = get_extension_for_hash(hash_value)
        return get_url_for_hash(hash_value, file_extension)
    
    # Replace thumbnail URLs
    S = re.sub(md5_pattern_thumbnail, replace_thumbnail, S)
    
    # Replace display none hashes
    S = re.sub(md5_pattern_data, replace_data, S)
    
    return S

def get_url_for_hash(hash, extension):
    base_url = "http://127.0.0.1:8000/static/images"
    directory_structure = f"{hash[:2]}/{hash[2:4]}/{hash}"
    return f"{base_url}/{directory_structure}.{extension}"

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


def remove_html_prefix(s):
    s = re.sub(r'```html', '', s)
    s = re.sub(r'```', '<br>', s)
    s = re.sub(r'### (.*)\n', r'<h2><strong>\1</strong></h2><br>\n', s)
    s = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', s)
    return s


def format_conversation_payload(conversation_payload: List[ConversationPayload]) -> str:
    # Format the conversation history into a single string
    formatted_history = ""
    for entry in conversation_payload:
        actor = entry.actor
        content = entry.content
        formatted_history += f"{actor}: {content}\n"
    return formatted_history.strip()



def perform_inference(inference_payload: InferencePayload) -> Generator[dict, None, None]:
    try:
        conversation_history = inference_payload.conversation_payload or []

        if inference_payload.conversation_payload:
            print("Received conversation payload")

        intent_data = determine_intent(inference_payload.query, conversation_history)
        parameters = intent_data.get('filter_parameters')
        print("Extracted parameters: ", parameters)
        required_outcomes = intent_data.get('required_outcomes')
        print("Required outcomes: ", required_outcomes)
        additional_requirements = intent_data.get('additional_requirements')
        print("Additional requirements: ", additional_requirements)

        if required_outcomes == [1]:
            required_outcomes = [1,2,3]
        if 0 in required_outcomes:
            yield {
                "response": "I am unable to provide a response to your query."
            }
            return 
        
        filtered_data = search_qdrant(parameters, inference_payload.query, conversation_history)

        print("Results sent to chatgpt:",filtered_data.total,filtered_data)
        if not filtered_data.results:
            yield {
                "response": "I couldn't find any relevant information based on your query. Could you please rephrase or provide more details?"
            }
            return

        output_parts = []
        # Use ThreadPoolExecutor to parallelize the calls
        with ThreadPoolExecutor() as executor:
            future_to_outcome = {
                executor.submit(get_insight_function(outcome), filtered_data, inference_payload.query, conversation_history): outcome
                for outcome in required_outcomes if outcome in [2, 3]  # Only campaign and creative insights
            }

            campaign_insights = ""
            creative_insights = ""

            for future in as_completed(future_to_outcome):
                outcome = future_to_outcome[future]
                try:
                    result = future.result()
                    if outcome == 2:
                        campaign_insights = result
                        output_parts.append(result)
                    elif outcome == 3:
                        creative_insights = result
                        output_parts.append(result)
                except Exception as e:
                    print(f"Error processing outcome {outcome}: {e}")

        # Now call media_plan with the gathered insights
        if 1 in required_outcomes:
            media_plan_result = media_plan(filtered_data, inference_payload.query, conversation_history, campaign_insights, creative_insights)
            output_parts.insert(0,media_plan_result)

        final_output = ''.join(output_parts)
        final_output = replace_hash_with_url(remove_html_prefix(final_output))
        yield {"response": final_output}

    except Exception as e:
        print(f"Error in perform_inference: {e}")
        yield {
            "response": "An error occurred while processing your request. Please try again later."
        }

def get_insight_function(outcome):
    """ Maps required outcomes to their corresponding functions. """
    mapping = {
        1: media_plan,          
        2: campaign_performance_insights, 
        3: creative_insights,
    }
    return mapping.get(outcome)