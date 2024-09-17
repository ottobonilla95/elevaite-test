from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue
from typing import Dict, Any, List
from openai import OpenAI
from model import AdCreative, SearchResult, InferencePayload, ConversationPayload
import os
import re
from dotenv import load_dotenv
import json

prompt1 = """
You are an AI assistant specialized in analyzing user queries about media marketing campaigns. Your task is to determine the user's intent and extract relevant parameters. Respond with a JSON object containing the following:

1. 'intent': Either 'mediaplan_generation' or 'search_performance'
   - Use 'mediaplan_generation' if the query is about creating or planning a new campaign
   - Use 'search_performance' if the query is about searching or analyzing existing campaign data

2. 'filter_parameters': Parameters to filter the database by. Possible parameters include:
   Numeric fields:
   - "file_size": Size of the file in bytes
   - "booked_measure_impressions": Number of impressions booked
   - "delivered_measure_impressions": Number of impressions actually delivered
   - "clicks": Number of clicks
   - "conversion": Number of conversions
   - "duration": Campaign duration in days (int)

   Text fields:
   - "file_type": Either 'video' or 'image'
   - "industry": Industry sector of the campaign (e.g., 'Fashion', 'Entertainment', 'Consumer Packaged Goods (CPG)', 'Fashion Retail', etc.)
   - "targeting": possible options are 'device_targeting', 'geo_targeting', 'bullseye_targeting', 'day_part_targeting', 'waypoint_targeting', 'waypoint_place_name_targeting' , 'waypoint_place_category_targeting'
   - "duration_category": possible options - 'long','short','medium'
   - "brand": Brand name associated with the campaign

Example:
User: "I want to run a medium length summer campaign for a shoe brand, can you suggest a media plan"
Response: {
  "intent": "mediaplan_generation",
  "filter_parameters": {
    "season_holiday": "summer",
    "duration_category": "medium"
  },
}

User: "I want to understand how fashion product brands have performed; can you show details on conversion and the type of creative ran along with the themes"
Response: {
  "intent": "search_performance",
  "filter_parameters": {
    "industry": "Fashion",
  },
}
Analyze the user query and provide a similar JSON response."""


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
            collection_name=os.getenv("COLLECTION_NAME", "media_creatives"),
            query_vector=query_vector,
            query_filter=search_filter,
            limit=100  # Increase the limit to ensure we have enough results to process
        )
        print("Initial search completed.")
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        return SearchResult(results=[], total=0)

    if not search_result:
        print("No results found with filters. Falling back to vector search.")
        try:
            search_result = Qclient.search(
                collection_name=os.getenv("COLLECTION_NAME", "media_creatives"),
                query_vector=query_vector,
                limit=100,
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
    if len(limited_results) < 5:
        print("Less than 5 results found with relevance threshold. Performing additional search.")
        try:
            additional_results = Qclient.search(
                collection_name="media_creatives",
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

            print(f"Number of final results: {len(final_results)}")
            if not final_results:
                return SearchResult(results=[], total=0)

            return SearchResult(results=final_results, total=len(final_results))
        except Exception as e:
            print(f"Error in additional search: {e}")
            return SearchResult(results=[], total=0)

    if len(limited_results) == 0:
        return SearchResult(results=[], total=0)

    return SearchResult(results=limited_results, total=len(limited_results))


def determine_intent(user_query: str, conversation_history: List[ConversationPayload]) -> dict:
    try:
        messages = [{"role": "system", "content": prompt1}]
        
        for message in conversation_history:
            messages.append({"role": message.actor, "content": message.content})
        
        messages.append({"role": "user", "content": user_query})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return json.loads(response.choices[0].message.content)
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
        formatted_ad += "---"
        formatted_results.append(formatted_ad)
    return "\n".join(formatted_results)

def generate_response(query: str, search_result: SearchResult, system_prompt: str, conversation_history: List[ConversationPayload]) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    
    for message in conversation_history:
        messages.append({"role": message.actor, "content": message.content})
    
    messages.append({"role": "user", "content": f"Query: {query}\n\nSearch Results: {format_search_results(search_result)}"})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1250,
            n=3,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in generating response: {e}")
        return "I apologize, but I couldn't generate a response at this time."


def media_plan_generation(filtered_data: SearchResult, query: str,conversation_history: List[ConversationPayload]) -> str:
    system_prompt = """
You are a media planning expert tasked with creating a comprehensive media plan based on historical creative performance data. Analyze the provided data, prioritizing creatives with similar contexts, then high conversion rates, and generate a detailed media plan in HTML table format. Follow these steps:
1. Evaluate the data and identify top-performing creatives based on conversion rates.(Display conversions rate with a '%' sign).
2. Develop a creative strategy drawing insights from the best-performing creatives.
3. Recommend targeting options from the following list: device_targeting, geo_targeting, bullseye_targeting, day_part_targeting, waypoint_targeting, waypoint_place_name_targeting, waypoint_place_category_targeting. Explain your choices.
4. Suggest an appropriate duration category (short, medium, or long) for the campaign.
5. Recommend the optimal content type (video or image) based on historical performance.
6. Propose the number of booked impressions to achieve the best performance (conversion).
7. If applicable, suggest a season or holiday to run the ad campaign.
(When duration category is mentioned, then say short is less than 7 days, medium is 7-30 days, long is greater than 30 days)
Present your media plan in an HTML table format with the following structure:
<style>
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    vertical-align: top;
  }
  th {
    background-color: #e75f33;
  }
  .wrap-text {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
    hyphens: auto;
  }
    .number-column {
    text-align: right;
  }
</style>

<table> <tr> <th>Media Plan Component</th> <th>Recommendation</th> <th>Rationale</th> </tr>
    <tr> <td>Creative Strategy</td> <td>[Your recommendation]</td> <td>[Your rationale]</td></tr> 
    <tr> <td>Targeting Options</td> <td>[Your recommendation]</td> <td>[Your rationale]</td> </tr>
    <tr> <td>Duration Category</td> <td>[Your recommendation]</td> <td>[Your rationale]</td> </tr> 
    <tr> <td>Content Type</td> <td>[Your recommendation]</td> <td>[Your rationale]</td> </tr>
    <tr> <td>Booked Impressions</td> <td>[Your recommendation]</td> <td>[Your rationale]</td> </tr> 
    <tr> <td>Season/Holiday</td> <td>[Your recommendation]</td> <td>[Your rationale]</td> </tr> 
</table>

After the table, provide a brief summary of your recommendations with the key data points that influenced your decisions. 

Then include references to atleast 1 data point for each campaign used in your analysis in the following format - 
 <table> <tr> <th>Brand Name</th> <th>Product Name</th> <th>Targeting Type</th> <th>Delivered Impressions</th> <th>Duration Category</th> </th> <th>Clicks</th> <th>Creative Details</th> </tr>
    <tr> <td>[Brand Name]</td> <td>[Product Name]</td> <td>[Targeting Type]</td> <td class="number-column">[delivered_measure_impressions]</td> <td>[duration_category]</td><td>[No. of Clicks]</td> <td>[Brief description of creative and performance]</td> </tr>
    <!-- Add more rows as needed -->
</table>
 
    """
    return generate_response(query, filtered_data, system_prompt,conversation_history)

def usual_rag_generation(filtered_data: SearchResult, query: str,conversation_history: List[ConversationPayload]) -> str:
    system_prompt = """
You are a data analysis assistant specializing in advertising campaign reports. Your task is to analyze the provided data on creatives, queries, and campaign performance, and generate a concise, informative HTML table summarizing key campaign details.
The table should always include the following columns:
1. Brand Name
2. Product Name
Other columns should be dynamically adjusted based on the data available and the query provided.
Here’s how to approach the table creation
1. Determine the Additional Columns: Based on the query and available data, identify which additional columns should be included. These could be metrics like Campaign Name, Targeting Type, Delivered Measure/Impressions, Creative Details, or any other relevant data. (Display conversions rate with a '%' sign).
2. Construct the Table: Create an HTML table with the essential columns (Brand Name and Product Name) and include the dynamically selected columns based on the query. Make sure each column accurately represents the available data.

<style>
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    vertical-align: top;
  }
  th {
    background-color: #e75f33;
  }
  .wrap-text {
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
    hyphens: auto;
  }
  .number-column {
    text-align: right;
  }
</style>
<table>
  <tr>
    <th>Brand Name</th>
    <th>Product Name</th>
    <!-- Include dynamically selected columns here -->
    <th>Additional Column 1</th>
    <th>Additional Column 2</th>
    <!-- Add more columns as needed -->
  </tr>
  <tr>
    <td>[Brand Name]</td>
    <td>[Product Name]</td>
    <!-- Include data for dynamically selected columns here -->
    <td>[Additional Data 1]</td>
    <td>[Additional Data 2]</td>
    <!-- Add more data as needed -->
  </tr>
  <!-- Add more rows as needed -->
</table>

Creative Insights: After the table, provide a short paragraph with qualitative insights about the creatives, such as:
1. Which creative styles or formats performed best.
2. Patterns in targeting that led to better performance.
3. Noteworthy differences between ordered and served impressions.
Please ensure that your analysis is based on the data provided, and that you highlight the most relevant and insightful information in your table and summary. Respond within 1000 tokens.
    """
    return generate_response(query, filtered_data, system_prompt,conversation_history)

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

def perform_inference(inference_payload: InferencePayload):
    try:
        print("Received Payload: ", inference_payload.query)
        conversation_history = inference_payload.conversation_payload or []

        if inference_payload.conversation_payload:
            print("Received conversation payload")
            print(conversation_history)

        intent_data = determine_intent(inference_payload.query, conversation_history)
        intent = intent_data.get('intent')
        print("Intent extracted: ", intent)
        parameters = intent_data.get('filter_parameters')
        print("Extracted parameters: ", parameters)

        filtered_data = search_qdrant(parameters, inference_payload.query, conversation_history)

        if not filtered_data.results:
            return {
                "response": "I couldn't find any relevant information based on your query. Could you please rephrase or provide more details?"
            }

        if intent == 'mediaplan_generation':
            output = media_plan_generation(filtered_data, inference_payload.query,conversation_history)
        elif intent == 'search_performance':
            output = usual_rag_generation(filtered_data, inference_payload.query,conversation_history)
        else:
            return {
                "response": "At the moment I am incapable of answering such questions."
            }
        
        output = remove_html_prefix(output)
        print("Output:", output)
        
        return {
            "response": output
        }
    except Exception as e:
        print(f"Error in perform_inference: {e}")
        return {
            "response": "An error occurred while processing your request. Please try again later."
        }
