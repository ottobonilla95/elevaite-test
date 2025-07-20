import os
import dotenv
import requests
import markdownify
from bs4 import BeautifulSoup
from utils import function_schema
from typing import Optional, Dict, Any, List
from utils import client
import pickle
import logging
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import re

SEGMENT_NUM = 5

dotenv.load_dotenv(".env.local")

GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")
CX_ID = os.getenv("CX_ID_PERSONAL")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

EXAMPLE_DATA = [
    {"customer_id": 1111, "order_number": 1720, "location": "New York"},
    {"customer_id": 2222, "order_number": 9, "location": "Los Angeles"},
    {"customer_id": 3333, "order_number": 45, "location": "Chicago"},
    {"customer_id": 4444, "order_number": 100, "location": "Miami"},
    {"customer_id": 5555, "order_number": 200, "location": "San Francisco"},
    {"customer_id": 6666, "order_number": 300, "location": "Seattle"},
    {"customer_id": 7777, "order_number": 400, "location": "Boston"},
    {"customer_id": 8888, "order_number": 500, "location": "Denver"},
    {"customer_id": 9999, "order_number": 600, "location": "Houston"},
]


@function_schema
def add_numbers(a: int, b: int) -> str:
    """
    Adds two numbers and returns the sum.
    """
    return f"The sum of {a} and {b} is {a + b}"


@function_schema
def get_customer_order(customer_id: int) -> str:
    """ "
    Returns the order number for a given customer ID."""
    if customer_id in [i["customer_id"] for i in EXAMPLE_DATA]:
        order_number = [
            i["order_number"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id
        ][0]
        return f"The order number for customer ID {customer_id} is {order_number}"
    return f"No order found for customer ID {customer_id}"


@function_schema
def get_customer_location(customer_id: int) -> str:
    """ "
    Returns the location for a given customer ID."""
    if customer_id in [i["customer_id"] for i in EXAMPLE_DATA]:
        location = [
            i["location"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id
        ][0]
        return f"The location for customer ID {customer_id} is {location}"
    return f"No location found for customer ID {customer_id}"


@function_schema
def add_customer(customer_id: int, order_number: int, location: str) -> str:
    """ "
    Adds a new customer to the database."""
    EXAMPLE_DATA.append(
        {"customer_id": customer_id, "order_number": order_number, "location": location}
    )
    return f"Customer ID {customer_id} added successfully."


@function_schema
def weather_forecast(location: str) -> str:
    """ "
    Returns the weather forecast for a given location. Only give one city at a time.
    """
    url = f"http://api.weatherstack.com/current?access_key={WEATHER_API_KEY}&query={location}"
    response = requests.get(url)

    if response.status_code != 200:
        return f"Error: Can't fetch weather data for {location}"
    else:
        data = response.json()
        return str(data)


@function_schema
def url_to_markdown(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("body")

        if content:
            markdown_content = markdownify.markdownify(
                str(content), heading_style="ATX"
            )
            return markdown_content[:20000]
        else:
            return "No content found in the webpage body."

    except requests.RequestException as e:
        return f"Error fetching URL: {e}"


@function_schema
def web_search(query: str, num: Optional[int] = 2) -> str:
    """
    You can use this tool to get any information from the web. Just type in your query and get the results.
    """
    num = 1
    # try:
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API}&cx={CX_ID}&num={num}"
    response = requests.get(url)
    print(response)
    urls = [i["link"] for i in response.json()["items"]]
    print(urls)
    text = "\n".join([url_to_markdown(i) for i in urls])
    # print(text)
    prompt = f"Use the following text to answer the given: {query} \n\n ---BEGIN WEB TEXT --- {text} ---BEGIN WEB TEXT --- "
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You're a web search agent."},
            {"role": "user", "content": prompt},
        ],
    )
    if response.choices[0].message.content is not None:
        return response.choices[0].message.content
    return ""


@function_schema
def print_to_console(text: str) -> str:
    """ "
    Prints the given text to the console.
    """
    print(text)
    return f"Printed {text} to the console."


@function_schema
def query_retriever2(query: str) -> list:
    """ "
    RETRIEVER TOOL

    Use this tool to query the Toshiba knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: "AC01548000"
    Example: "4348"
    Example: "What is TAL"
    Example: "assembly name for part number 3AC01548000"
    Example: "TAL parts list"
    """
    RETRIEVER_URL = os.getenv("RETRIEVER_URL")
    if RETRIEVER_URL is None:
        raise ValueError(
            "RETRIEVER_URL not found. Please set it in the environment variables."
        )
    url = RETRIEVER_URL + "/query-chunks"
    params = {"query": query, "top_k": 60}

    # Make the POST request
    response = requests.post(url, params=params)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    sources = []
    segments = response.json()["selected_segments"][:4]
    for i, segment in enumerate(segments):
        res += "*" * 5 + f"\n\nSegment {i}" + "\n" + "Contextual Header: "
        contextual_header = segment["chunks"][0].get("contextual_header", "")
        skip_length = len(contextual_header) if contextual_header else 0
        res += (
            contextual_header
            if contextual_header
            else "No contextual header" + "\n" + "Context: " + "\n"
        )
        # print(segment["score"])
        print("Segment Done")
        references = ""
        for j, chunk in enumerate(segment["chunks"]):
            # res += f"Contextual Header: {chunk['contextual_header']}\n"
            res += chunk["chunk_text"][skip_length:]
            references += f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n"
            sources.append(f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n")
            # res += "\n"
        res += f"References: {references}"
    res += "\n\n" + "-" * 5 + "\n\n"
    print(res)
    return [res, sources]


@function_schema
def media_context_retriever(
    query: str,
    collection_name: str = "media_data_standardized_v2",
    limit: Optional[int] = 10,
    filter_params: Optional[str] = None,
) -> str:
    """
    MEDIA CONTEXT RETRIEVER TOOL

    Use this tool to retrieve relevant media campaign context and data using semantic search.
    Searches through historical media campaigns, creatives, and performance data to find similar contexts.

    Args:
        query: The search query text for finding relevant media context
        collection_name: Name of the media data collection to search (default: 'media_data_standardized_v2')
        limit: Maximum number of results to return (default: 10)
        filter_params: Optional JSON string with filter parameters (e.g., '{"brand": "nike", "industry": "Fashion & Retail"}')

    EXAMPLES:
    Example: media_context_retriever("high performing fashion campaigns")
    Example: media_context_retriever("summer beverage ads", "media_data_standardized_v2", 10, '{"season": "summer", "industry": "Food & Beverage"}')
    Example: media_context_retriever("Nike campaigns with high CTR", "media_data_standardized_v2", 8, '{"brand": "nike"}')
    """

    try:
        from qdrant_client import QdrantClient

        # Get environment variables
        QDRANT_HOST = os.getenv("QDRANT_HOST", "http://3.101.65.253")
        QDRANT_PORT = os.getenv("QDRANT_PORT", "5333")
        COLLECTION_NAME = os.getenv("COLLECTION_NAME", "media_data_standardized_v2")

        # Use provided collection_name or default
        collection = collection_name or COLLECTION_NAME

        # Initialize Qdrant client
        qdrant_url = f"{QDRANT_HOST}:{QDRANT_PORT}"
        qdrant_client = QdrantClient(url=qdrant_url)

        # Get embedding for query using OpenAI
        embedding_response = client.embeddings.create(
            model="text-embedding-ada-002", input=query
        )
        query_vector = embedding_response.data[0].embedding

        # Parse filter parameters - temporarily disabled due to Qdrant compatibility issues
        # filter_dict = None
        # if filter_params:
        #     try:
        #         filter_dict = json.loads(filter_params)
        #     except json.JSONDecodeError:
        #         print(f"Warning: Invalid filter_params JSON: {filter_params}")

        # Perform search without filters for now
        search_results = qdrant_client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            # query_filter=filter_dict,  # Temporarily disabled
            with_payload=True,
        )

        # Format results
        if search_results is None or not search_results:
            return f"No results found for query: '{query}' in collection '{collection}'"

        result_text = (
            f"QDRANT SEARCH RESULTS for '{query}' (Collection: {collection}):\n\n"
        )
        for i, result in enumerate(search_results):
            payload = result.payload
            score = result.score

            # Handle case where payload might be None
            if payload is None:
                result_text += f"Result {i+1} (Score: {round(score, 3)}):\n"
                result_text += "No payload data available\n"
                result_text += "-" * 50 + "\n"
                continue

            result_text += f"Result {i+1} (Score: {round(score, 3)}):\n"

            # Use correct field names based on AdCreative model
            result_text += f"Campaign Folder: {payload.get('campaign_folder', 'Unknown Campaign')}\n"
            result_text += f"File Name: {payload.get('file_name', 'Unknown File')}\n"
            result_text += f"Brand: {payload.get('brand', 'Unknown Brand')}\n"
            result_text += f"Industry: {payload.get('industry', 'Unknown Industry')}\n"
            result_text += f"File Type: {payload.get('file_type', 'Unknown')}\n"
            result_text += f"Duration: {payload.get('duration(days)', 0)} days\n"
            result_text += (
                f"Duration Category: {payload.get('duration_category', 'Unknown')}\n"
            )
            result_text += (
                f"Season/Holiday: {payload.get('season_holiday', 'Unknown')}\n"
            )
            result_text += f"Ad Objective: {payload.get('ad_objective', 'Unknown')}\n"
            result_text += f"Targeting: {payload.get('targeting', 'Unknown')}\n"
            result_text += f"Tone/Mood: {payload.get('tone_mood', 'Unknown')}\n"

            # Performance metrics
            booked_impressions = payload.get("booked_measure_impressions", 0)
            delivered_impressions = payload.get("delivered_measure_impressions", 0)
            clicks = payload.get("clicks", 0)
            conversion = payload.get("conversion", 0)

            # Calculate budget as 0.05 * booked_impressions
            budget = 0.05 * booked_impressions if booked_impressions else 0

            result_text += f"Booked Impressions: {booked_impressions:,}\n"
            result_text += f"Delivered Impressions: {delivered_impressions:,}\n"
            result_text += f"Clicks: {clicks:,}\n"
            result_text += f"Conversion: {conversion}\n"
            result_text += f"Budget: ${budget:,.2f}\n"

            # Calculate CTR if we have the data
            if delivered_impressions > 0 and clicks > 0:
                ctr = (clicks / delivered_impressions) * 100
                result_text += f"CTR: {ctr:.2f}%\n"
            else:
                result_text += f"CTR: N/A\n"

            result_text += "-" * 50 + "\n"

        return result_text

    except Exception as e:
        print(f"Qdrant search error: {e}")
        import traceback

        traceback.print_exc()
        # Fallback to mock data for development
        mock_results = [
            {
                "campaign_name": "Nike Summer Collection 2024",
                "brand": "Nike",
                "industry": "Fashion & Retail",
                "budget": 45000,
                "duration": 30,
                "ctr": 2.1,
                "conversion_rate": 1.8,
                "impressions": 850000,
                "score": 0.95,
            },
            {
                "campaign_name": "Adidas Athletic Wear Campaign",
                "brand": "Adidas",
                "industry": "Fashion & Retail",
                "budget": 38000,
                "duration": 25,
                "ctr": 1.9,
                "conversion_rate": 1.6,
                "impressions": 720000,
                "score": 0.87,
            },
        ]

        result_text = (
            f"QDRANT SEARCH RESULTS for '{query}' (MOCK DATA - Connection Error):\n\n"
        )
        for i, result in enumerate(mock_results[:limit]):
            result_text += f"Result {i+1} (Score: {result['score']}):\n"
            result_text += f"Campaign: {result['campaign_name']}\n"
            result_text += f"Brand: {result['brand']}\n"
            result_text += f"Industry: {result['industry']}\n"
            result_text += f"Budget: ${result['budget']:,}\n"
            result_text += f"Duration: {result['duration']} days\n"
            result_text += f"CTR: {result['ctr']}%\n"
            result_text += f"Conversion Rate: {result['conversion_rate']}%\n"
            result_text += f"Impressions: {result['impressions']:,}\n"
            result_text += "-" * 50 + "\n"

        return result_text


@function_schema
def redis_cache_operation(
    operation: str, key: str, value: Optional[str] = None, ttl: Optional[int] = None
) -> str:
    """
    REDIS CACHE TOOL

    Use this tool to perform Redis cache operations for storing and retrieving data.

    Args:
        operation: The Redis operation to perform ('get', 'set', 'delete', 'exists', 'keys')
        key: The Redis key to operate on
        value: The value to set (required for 'set' operation)
        ttl: Time to live in seconds for 'set' operation (optional)

    EXAMPLES:
    Example: redis_cache_operation("set", "campaign:nike:performance", '{"ctr": 0.045, "clicks": 15420}', 3600)
    Example: redis_cache_operation("get", "campaign:nike:performance")
    Example: redis_cache_operation("delete", "campaign:nike:performance")
    Example: redis_cache_operation("keys", "campaign:*")
    Example: redis_cache_operation("exists", "user:session:12345")
    """
    # Mock implementation - in real scenario this would connect to Redis
    print(f"Redis operation: {operation} on key: {key}")

    if operation == "set":
        if value is None:
            return "Error: Value is required for SET operation"
        ttl_info = f" with TTL {ttl}s" if ttl else ""
        print(f"Setting key '{key}' = '{value}'{ttl_info}")
        return f"Successfully set key '{key}' in Redis{ttl_info}"

    elif operation == "get":
        # Mock cached data
        mock_cache = {
            "campaign:nike:performance": '{"ctr": 0.045, "clicks": 15420, "impressions": 342000}',
            "campaign:cocacola:metrics": '{"ctr": 0.038, "clicks": 12800, "impressions": 337000}',
            "user:session:12345": '{"user_id": 12345, "login_time": "2024-01-15T10:30:00Z"}',
            "targeting:config:tech_professionals": '{"age_range": ["25-44"], "interests": ["Technology"]}',
        }

        if key in mock_cache:
            return f"Retrieved from Redis - Key: '{key}', Value: {mock_cache[key]}"
        else:
            return f"Key '{key}' not found in Redis cache"

    elif operation == "delete":
        print(f"Deleting key '{key}' from Redis")
        return f"Successfully deleted key '{key}' from Redis"

    elif operation == "exists":
        # Mock existence check
        existing_keys = [
            "campaign:nike:performance",
            "user:session:12345",
            "targeting:config:tech_professionals",
        ]
        exists = key in existing_keys
        return f"Key '{key}' {'exists' if exists else 'does not exist'} in Redis"

    elif operation == "keys":
        # Mock pattern matching
        mock_keys = [
            "campaign:nike:performance",
            "campaign:cocacola:metrics",
            "campaign:disney:analytics",
            "user:session:12345",
            "targeting:config:tech_professionals",
        ]

        if "*" in key:
            pattern = key.replace("*", "")
            matching_keys = [k for k in mock_keys if k.startswith(pattern)]
            return f"Keys matching pattern '{key}': {matching_keys}"
        else:
            return f"Exact key search: {[key] if key in mock_keys else []}"

    else:
        return f"Error: Unsupported Redis operation '{operation}'. Supported: get, set, delete, exists, keys"


@function_schema
def postgres_query(
    query_type: str,
    table: str,
    conditions: Optional[str] = None,
    data: Optional[str] = None,
    limit: Optional[int] = 10,
) -> str:
    """
    POSTGRES DATABASE TOOL

    Use this tool to perform PostgreSQL database operations for campaign and user data.

    Args:
        query_type: Type of SQL operation ('select', 'insert', 'update', 'delete', 'count')
        table: Database table name (e.g., 'campaigns', 'users', 'targeting_configs', 'performance_metrics')
        conditions: WHERE clause conditions (e.g., 'brand = "nike" AND season = "summer"')
        data: JSON string with data for insert/update operations
        limit: Maximum number of results for select queries (default: 10)

    EXAMPLES:
    Example: postgres_query("select", "campaigns", "brand = 'nike' AND conversion_rate > 0.04", limit=5)
    Example: postgres_query("insert", "campaigns", data='{"name": "Summer Campaign", "brand": "nike", "budget": 25000}')
    Example: postgres_query("update", "campaigns", "id = 123", '{"status": "completed", "end_date": "2024-01-15"}')
    Example: postgres_query("count", "campaigns", "industry = 'Fashion & Retail'")
    Example: postgres_query("delete", "campaigns", "id = 456")
    """
    # Mock implementation - in real scenario this would connect to PostgreSQL
    print(f"PostgreSQL {query_type.upper()} operation on table '{table}'")
    if conditions:
        print(f"Conditions: {conditions}")
    if data:
        print(f"Data: {data}")

    # Mock database tables and data
    mock_campaigns = [
        {
            "id": 1,
            "name": "Summer Fashion 2024",
            "brand": "nike",
            "industry": "Fashion & Retail",
            "conversion_rate": 0.045,
            "budget": 25000,
            "status": "active",
        },
        {
            "id": 2,
            "name": "Holiday Beverages",
            "brand": "coca-cola",
            "industry": "Food & Beverage",
            "conversion_rate": 0.038,
            "budget": 18000,
            "status": "completed",
        },
        {
            "id": 3,
            "name": "Tech Innovation",
            "brand": "apple",
            "industry": "Technology & Telecommunications",
            "conversion_rate": 0.052,
            "budget": 35000,
            "status": "active",
        },
        {
            "id": 4,
            "name": "Automotive Excellence",
            "brand": "toyota",
            "industry": "Automotive",
            "conversion_rate": 0.041,
            "budget": 22000,
            "status": "paused",
        },
    ]

    mock_users = [
        {
            "id": 101,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "campaign_manager",
            "created_at": "2024-01-10",
        },
        {
            "id": 102,
            "username": "jane_smith",
            "email": "jane@example.com",
            "role": "analyst",
            "created_at": "2024-01-12",
        },
    ]

    if query_type == "select":
        if table == "campaigns":
            results = mock_campaigns[:limit]
            result_text = f"SELECT results from '{table}' table:\n"
            for row in results:
                result_text += f"ID: {row['id']}, Name: {row['name']}, Brand: {row['brand']}, CTR: {row['conversion_rate']}, Budget: ${row['budget']}\n"
            return result_text
        elif table == "users":
            results = mock_users[:limit]
            result_text = f"SELECT results from '{table}' table:\n"
            for row in results:
                result_text += f"ID: {row['id']}, Username: {row['username']}, Email: {row['email']}, Role: {row['role']}\n"
            return result_text
        else:
            return f"Mock data not available for table '{table}'"

    elif query_type == "insert":
        return (
            f"Successfully inserted new record into '{table}' table with data: {data}"
        )

    elif query_type == "update":
        return f"Successfully updated records in '{table}' table where {conditions} with data: {data}"

    elif query_type == "delete":
        return f"Successfully deleted records from '{table}' table where {conditions}"

    elif query_type == "count":
        if table == "campaigns":
            count = len(mock_campaigns)
        elif table == "users":
            count = len(mock_users)
        else:
            count = 0
        return f"COUNT result for '{table}' table: {count} records"

    else:
        return f"Error: Unsupported query type '{query_type}'. Supported: select, insert, update, delete, count"


@function_schema
def image_generation(
    prompt: str,
    operation_type: str,
    dimensions: Optional[str] = "1024x1024",
    reference_image_url: Optional[str] = None,
    aspect_ratio: Optional[str] = "1:1",
    count: Optional[int] = 1,
    iab_size: Optional[str] = None,
) -> str:
    """
    IMAGE GENERATION TOOL

    Use this tool to generate, resize, or manipulate images for marketing campaigns and creative content.

    Args:
        prompt: Text description for image generation or operation details
        operation_type: Type of operation ('generate', 'resize', 'multi_generate', 'resize_to_iab')
        dimensions: Image dimensions in 'widthxheight' format (e.g., '1024x1024', '1920x1080')
        reference_image_url: URL of reference image for resize operations (optional)
        aspect_ratio: Aspect ratio for generation ('1:1', '3:4', '4:3', '9:16', '16:9')
        count: Number of images to generate for multi_generate (1-4, default: 1)
        iab_size: IAB standard size name for resize_to_iab operation

    Supported Operations:
    - 'generate': Create new image from text prompt
    - 'resize': Resize existing image to new dimensions
    - 'multi_generate': Generate multiple variations of an image
    - 'resize_to_iab': Resize to standard IAB advertising sizes

    Standard Dimensions:
    - Square: 1024x1024, 512x512
    - Portrait: 768x1024, 576x1024
    - Landscape: 1024x768, 1024x576
    - Social Media: 1080x1080 (Instagram), 1200x630 (Facebook)

    IAB Standard Sizes:
    - Banner: 728x90, Leaderboard: 728x90
    - Rectangle: 300x250, Large Rectangle: 336x280
    - Skyscraper: 160x600, Wide Skyscraper: 300x600
    - Mobile Banner: 320x50, Large Mobile Banner: 320x100

    EXAMPLES:
    Example: image_generation("Modern minimalist product showcase with clean lighting", "generate", "1024x1024", aspect_ratio="1:1")
    Example: image_generation("Fashion brand summer campaign", "multi_generate", "1080x1080", count=3)
    Example: image_generation("Resize campaign image", "resize", "728x90", reference_image_url="https://example.com/image.jpg")
    Example: image_generation("Convert to banner", "resize_to_iab", iab_size="Banner")
    """
    # Mock implementation - in real scenario this would connect to image generation API
    print(f"Image Generation: {operation_type} operation")
    print(f"Prompt: {prompt}")
    print(f"Dimensions: {dimensions}")
    print(f"Aspect Ratio: {aspect_ratio}")

    # Mock response based on operation type
    if operation_type == "generate":
        mock_image_url = (
            f"https://mock-api.com/generated-image-{hash(prompt) % 10000}.jpg"
        )
        return f"Successfully generated image with prompt: '{prompt}'\nDimensions: {dimensions}\nAspect Ratio: {aspect_ratio}\nGenerated Image URL: {mock_image_url}\nImage ID: IMG_{hash(prompt) % 100000}"

    elif operation_type == "multi_generate":
        mock_urls = []
        for i in range(min(count, 4)):
            mock_urls.append(
                f"https://mock-api.com/generated-image-{hash(prompt) % 10000}-variant-{i+1}.jpg"
            )

        result = f"Successfully generated {len(mock_urls)} image variations with prompt: '{prompt}'\n"
        result += f"Dimensions: {dimensions}\nAspect Ratio: {aspect_ratio}\n"
        result += "Generated Images:\n"
        for i, url in enumerate(mock_urls):
            result += (
                f"  Variant {i+1}: {url} (ID: IMG_{hash(prompt + str(i)) % 100000})\n"
            )
        return result

    elif operation_type == "resize":
        if reference_image_url:
            mock_resized_url = f"https://mock-api.com/resized-image-{hash(reference_image_url) % 10000}.jpg"
            return f"Successfully resized image from: {reference_image_url}\nNew Dimensions: {dimensions}\nResized Image URL: {mock_resized_url}\nImage ID: IMG_{hash(reference_image_url) % 100000}_resized"
        else:
            return "Error: Reference image URL is required for resize operation"

    elif operation_type == "resize_to_iab":
        if not iab_size:
            return "Error: IAB size is required for resize_to_iab operation"

        # Mock IAB size mappings
        iab_dimensions = {
            "Banner": "728x90",
            "Leaderboard": "728x90",
            "Rectangle": "300x250",
            "Large Rectangle": "336x280",
            "Skyscraper": "160x600",
            "Wide Skyscraper": "300x600",
            "Mobile Banner": "320x50",
            "Large Mobile Banner": "320x100",
        }

        if iab_size in iab_dimensions:
            actual_dimensions = iab_dimensions[iab_size]
            mock_iab_url = f"https://mock-api.com/iab-resized-{iab_size.lower().replace(' ', '-')}-{hash(prompt) % 10000}.jpg"
            return f"Successfully resized image to IAB standard: {iab_size}\nDimensions: {actual_dimensions}\nIAB Resized Image URL: {mock_iab_url}\nImage ID: IMG_{hash(prompt + iab_size) % 100000}_iab"
        else:
            return f"Error: Unsupported IAB size '{iab_size}'. Supported sizes: {', '.join(iab_dimensions.keys())}"

    else:
        return f"Error: Unsupported operation type '{operation_type}'. Supported: generate, resize, multi_generate, resize_to_iab"


def _get_google_credentials():
    """Get OAuth credentials from token.pickle with automatic refresh"""
    logger = logging.getLogger(__name__)

    creds = None
    if os.path.exists("token.pickle"):
        try:
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)

        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return None

    return creds


def _create_google_drive_folder(
    service, folder_name: str, parent_folder_id: str
) -> Dict[str, Any]:
    """Create a folder in Google Drive"""
    try:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }

        folder = (
            service.files()
            .create(
                body=file_metadata, supportsAllDrives=True, fields="id, webViewLink"
            )
            .execute()
        )

        return {"id": folder.get("id"), "link": folder.get("webViewLink")}
    except Exception as e:
        raise Exception(f"Failed to create folder: {str(e)}")


def _share_folder_with_users(service, folder_id: str, emails: List[str]):
    """Share a folder with iopex.com domain (ignores individual emails)"""
    try:
        # Share with entire iopex.com domain instead of individual emails
        permission = {
            "type": "domain",
            "role": "writer",
            "domain": "iopex.com"
        }
        service.permissions().create(
            fileId=folder_id, body=permission, supportsAllDrives=True
        ).execute()
        logging.getLogger(__name__).info(f"Shared folder {folder_id} with iopex.com domain")
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Failed to share with iopex.com domain: {str(e)}"
        )


def _extract_targeting_info_from_placement(
    placement_info: Dict[str, Any],
) -> Dict[str, str]:
    """Extract targeting information from placement data"""
    # Default values
    targeting_info = {
        "age_range": "Not specified",
        "gender": "Not specified",
        "income_level": "Not specified",
        "interests": "Not specified",
        "location": "Not specified",
        "behavioral_data": "Not specified",
    }

    # Check for simple targeting format
    if "targeting" in placement_info:
        targeting = placement_info["targeting"]
        if isinstance(targeting, dict):
            targeting_info.update(
                {
                    "age_range": targeting.get("age_range", "Not specified"),
                    "gender": targeting.get("gender", "Not specified"),
                    "income_level": targeting.get("income_level", "Not specified"),
                    "interests": targeting.get("interests", "Not specified"),
                    "location": targeting.get("location", "Not specified"),
                    "behavioral_data": targeting.get("behavioral_data", "Not specified"),
                }
            )
        elif isinstance(targeting, str):
            # If targeting is a string, use it for all fields
            targeting_info = {
                "age_range": targeting,
                "gender": targeting,
                "income_level": targeting,
                "interests": targeting,
                "location": targeting,
                "behavioral_data": targeting,
            }

    return targeting_info


def _generate_pdf_with_media_plan_table(
    drive_service,
    docs_service,
    template_id: str,
    folder_id: str,
    filename: str,
    template_variables: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate PDF from template with Media Plan table support"""
    try:
        # Copy the template document (as Google Doc first)
        copied_doc = (
            drive_service.files()
            .copy(
                fileId=template_id,
                body={"name": f"{filename}_temp_doc", "parents": [folder_id]},
                supportsAllDrives=True,
            )
            .execute()
        )

        doc_id = copied_doc["id"]

        # Handle regular text replacements first (excluding media_plan_table)
        requests = []
        table_data = None

        for key, value in template_variables.items():
            if key == "media_plan_table":
                # Store table data for special handling
                table_data = value
            else:
                # Regular text replacement
                requests.append(
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{" + key + "}}",
                                "matchCase": True,
                            },
                            "replaceText": str(value),
                        }
                    }
                )

        # Execute regular text replacements first
        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

        # Handle table insertion if media_plan_table data exists
        if table_data:
            _insert_media_plan_table_simple(docs_service, doc_id, table_data)

        # Export the Google Doc as PDF
        pdf_export_url = (
            f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"
        )

        # Download the PDF content
        import io
        from googleapiclient.http import MediaIoBaseDownload

        request = drive_service.files().export_media(
            fileId=doc_id, mimeType="application/pdf"
        )
        pdf_content = io.BytesIO()
        downloader = MediaIoBaseDownload(pdf_content, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()

        # Upload the PDF content as a new file
        pdf_content.seek(0)
        from googleapiclient.http import MediaIoBaseUpload

        media = MediaIoBaseUpload(pdf_content, mimetype="application/pdf")
        pdf_file = (
            drive_service.files()
            .create(
                body={"name": f"{filename}.pdf", "parents": [folder_id]},
                media_body=media,
                supportsAllDrives=True,
                fields="id, webViewLink",
            )
            .execute()
        )

        # Delete the temporary Google Doc
        drive_service.files().delete(fileId=doc_id, supportsAllDrives=True).execute()

        return {"pdf_file_id": pdf_file["id"], "pdf_link": pdf_file["webViewLink"]}

    except Exception as e:
        raise Exception(f"Failed to generate PDF: {str(e)}")


def _insert_media_plan_table_simple(
    docs_service, doc_id: str, table_data: Dict[str, Any]
):
    """Insert a proper Google Docs table using the approach from tanaikech's implementation"""
    try:
        logger = logging.getLogger(__name__)
        logger.info("Starting media plan table insertion...")

        # Prepare table data
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])

        if not headers or not rows:
            logger.warning("No table headers or rows provided for media_plan_table")
            _fallback_text_replacement(docs_service, doc_id, table_data)
            return

        logger.info(
            f"Creating table with {len(headers)} columns and {len(rows) + 1} rows"
        )
        logger.info(f"Headers: {headers}")

        # Find the {{media_plan_table}} placeholder
        placeholder_text = "{{media_plan_table}}"
        placeholder_index = _find_placeholder_index(
            docs_service, doc_id, placeholder_text
        )

        if placeholder_index is None:
            logger.warning("{{media_plan_table}} placeholder not found in document")
            _fallback_text_replacement(docs_service, doc_id, table_data)
            return

        logger.info(f"Found placeholder at index {placeholder_index}")

        # Create and populate table
        _create_and_populate_table(
            docs_service, doc_id, placeholder_index, placeholder_text, headers, rows
        )

    except Exception as e:
        logging.getLogger(__name__).error(f"Error inserting media plan table: {str(e)}")
        # Fallback to simple text replacement
        _fallback_text_replacement(docs_service, doc_id, table_data)


def _find_placeholder_index(docs_service, doc_id: str, placeholder_text: str) -> int:
    """Find the index of the placeholder text in the document"""
    doc = docs_service.documents().get(documentId=doc_id).execute()

    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            paragraph = element["paragraph"]
            for text_element in paragraph.get("elements", []):
                if "textRun" in text_element:
                    text_content = text_element["textRun"].get("content", "")
                    if placeholder_text in text_content:
                        return text_element.get("startIndex")
    return None


def _create_and_populate_table(
    docs_service,
    doc_id: str,
    placeholder_index: int,
    placeholder_text: str,
    headers: list,
    rows: list,
):
    """Create table and populate it using the Tanaikech approach with calculated indices"""
    try:
        logger = logging.getLogger(__name__)
        # Calculate required dimensions
        num_rows = len(rows) + 1  # +1 for header row
        num_cols = len(headers)

        logger.info(f"Creating table with {num_rows} rows and {num_cols} columns")

        # Prepare all table data (headers + rows)
        all_table_data = [headers] + rows

        # Create requests using the Tanaikech approach
        requests = _create_table_requests(
            placeholder_index, placeholder_text, all_table_data
        )

        # Execute all requests in one batch
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()

        logger.info(
            f"Successfully created and populated table with {len(headers)} headers and {len(rows)} data rows"
        )

    except Exception as e:
        logging.getLogger(__name__).error(
            f"Error creating and populating table: {str(e)}"
        )
        raise


def _create_table_requests(
    placeholder_index: int, placeholder_text: str, table_data: list
):
    """Create requests for table creation and population using the Tanaikech approach"""
    try:
        logger = logging.getLogger(__name__)
        if not table_data or not table_data[0]:
            return []

        num_rows = len(table_data)
        max_cols = max(len(row) for row in table_data)

        logger.info(
            f"Creating table requests for {num_rows} rows and {max_cols} columns"
        )

        # Start with deleting the placeholder and creating the table
        requests = [
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": placeholder_index,
                        "endIndex": placeholder_index + len(placeholder_text),
                    }
                }
            },
            {
                "insertTable": {
                    "location": {"index": placeholder_index},
                    "rows": num_rows,
                    "columns": max_cols,
                }
            },
        ]

        # Calculate cell indices and create insertion requests using the improved Tanaikech approach
        table_index = placeholder_index
        index = table_index + 5  # Table starts at index + 5

        cell_requests = []

        # Process each row to calculate indices correctly
        for row_idx, row_data in enumerate(table_data):
            row_index = (
                index + (0 if row_idx == 0 else 3) - 1
            )  # First row: index, subsequent rows: index + 3 - 1

            # Process each cell in the row
            for col_idx, cell_value in enumerate(row_data):
                cell_index = row_index + col_idx * 2
                cell_value_str = str(cell_value)

                logger.info(
                    f"Adding cell [{row_idx}][{col_idx}] = '{cell_value_str}' at index {cell_index}"
                )

                # Add text insertion request
                cell_requests.append(
                    {
                        "insertText": {
                            "text": cell_value_str,
                            "location": {"index": cell_index},
                        }
                    }
                )

                # Make header row bold
                if row_idx == 0:
                    cell_requests.append(
                        {
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": cell_index,
                                    "endIndex": cell_index + len(cell_value_str),
                                },
                                "textStyle": {"bold": True},
                                "fields": "bold",
                            }
                        }
                    )

                index = cell_index + 1

            # Adjust index for missing columns in this row
            if len(row_data) < max_cols:
                index += (max_cols - len(row_data)) * 2

        # Reverse the cell requests (insert from bottom-right to top-left)
        cell_requests.reverse()

        # Add cell requests to the main requests
        requests.extend(cell_requests)

        logger.info(
            f"Created {len(requests)} total requests for table creation and population"
        )
        return requests

    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating table requests: {str(e)}")
        raise


def _fallback_text_replacement(docs_service, doc_id: str, table_data: Dict[str, Any]):
    """Fallback method to replace {{media_plan_table}} with formatted text if table insertion fails"""
    try:
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])

        if not headers or not rows:
            fallback_text = "No table data available"
        else:
            # Create a simple text table
            lines = []

            # Add headers
            lines.append(" | ".join(str(header) for header in headers))
            lines.append("-" * 50)  # Separator line

            # Add rows
            for row in rows:
                if isinstance(row, list):
                    lines.append(" | ".join(str(cell) for cell in row))
                else:
                    lines.append(str(row))

            fallback_text = "\n".join(lines)

        # Replace the placeholder with formatted text
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": "{{media_plan_table}}", "matchCase": True},
                    "replaceText": fallback_text,
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()

    except Exception as e:
        logging.getLogger(__name__).error(
            f"Error in fallback text replacement: {str(e)}"
        )


def _create_sheet_from_template(
    drive_service,
    sheets_service,
    folder_id: str,
    sheet_name: str,
    template_id: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new sheet by copying a template and populating it with data"""
    try:
        # Copy the template to create a new sheet
        copied_sheet = (
            drive_service.files()
            .copy(
                fileId=template_id,
                body={"name": sheet_name, "parents": [folder_id]},
                supportsAllDrives=True,
                fields="id, webViewLink",
            )
            .execute()
        )

        sheet_id = copied_sheet["id"]

        # Get the template headers from row 1
        header_result = (
            sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=sheet_id,
                range="A1:AA1",  # Headers from A to AA
                majorDimension="ROWS",
            )
            .execute()
        )

        headers = (
            header_result.get("values", [[]])[0] if header_result.get("values") else []
        )

        # Create a mapping of data to column positions
        updates = []
        for col_index, header in enumerate(headers):
            if header.lower().replace(" ", "_") in data:
                col_letter = chr(65 + col_index)  # Convert to A, B, C, etc.
                cell_range = f"{col_letter}2"  # Row 2 for data
                value = str(data[header.lower().replace(" ", "_")])
                updates.append({"range": cell_range, "values": [[value]]})

        # Batch update the sheet
        if updates:
            body = {"valueInputOption": "RAW", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id, body=body
            ).execute()

        return {"sheet_id": sheet_id, "sheet_link": copied_sheet["webViewLink"]}
    except Exception as e:
        raise Exception(f"Failed to create sheet from template: {str(e)}")


def _generate_pdf_from_template(
    drive_service,
    docs_service,
    template_id: str,
    output_folder_id: str,
    filename: str,
    template_variables: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate PDF from Google Docs template"""
    try:
        # Create a copy of the template
        copied_doc = (
            drive_service.files()
            .copy(
                fileId=template_id,
                body={"name": f"{filename}_temp_doc", "parents": [output_folder_id]},
                supportsAllDrives=True,
            )
            .execute()
        )

        doc_id = copied_doc["id"]

        # Replace placeholders in the document
        requests_list = []
        for placeholder, value in template_variables.items():
            requests_list.append(
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": f"{{{{{placeholder}}}}}",  # {{placeholder}} format
                            "matchCase": False,
                        },
                        "replaceText": str(value),
                    }
                }
            )

        if requests_list:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests_list}
            ).execute()

        # Export as PDF
        pdf_export = (
            drive_service.files()
            .export(fileId=doc_id, mimeType="application/pdf")
            .execute()
        )

        # Create PDF file in Drive
        pdf_metadata = {"name": f"{filename}.pdf", "parents": [output_folder_id]}

        # Upload PDF content
        from googleapiclient.http import MediaIoBaseUpload
        import io

        pdf_file = (
            drive_service.files()
            .create(
                body=pdf_metadata,
                media_body=MediaIoBaseUpload(
                    io.BytesIO(pdf_export), mimetype="application/pdf"
                ),
                supportsAllDrives=True,
                fields="id, webViewLink",
            )
            .execute()
        )

        # Delete the temporary document
        drive_service.files().delete(fileId=doc_id, supportsAllDrives=True).execute()

        return {"pdf_file_id": pdf_file["id"], "pdf_link": pdf_file["webViewLink"]}
    except Exception as e:
        raise Exception(f"Failed to generate PDF: {str(e)}")


@function_schema
def create_insertion_order(
    order_number: str,
    campaign_name: str,
    brand: str,
    customer_approver: str,
    customer_approver_email: str,
    sales_owner: str,
    sales_owner_email: str,
    fulfillment_owner: str,
    fulfillment_owner_email: str,
    objective_description: str,
    placement_data: str,
    base_folder_id: Optional[str] = None,
    sheet_template_id: Optional[str] = None,
    pdf_template_id: Optional[str] = None,
) -> str:
    """
    CREATE INSERTION ORDER IN GOOGLE DRIVE

    Creates a complete insertion order with Google Drive folder, Google Sheet, and PDF document.
    This tool automates the entire insertion order creation process including:
    - Creating a campaign folder in Google Drive
    - Generating a Google Sheet from a template with order details
    - Creating a PDF document from a template with Media Plan table
    - Sharing all resources with stakeholders

    Args:
        order_number: The insertion order number (e.g., "IO-340371-3439")
        campaign_name: Name of the marketing campaign
        brand: Brand name for the campaign
        customer_approver: Name of the customer approver
        customer_approver_email: Email address of the customer approver
        sales_owner: Name of the sales owner
        sales_owner_email: Email address of the sales owner
        fulfillment_owner: Name of the fulfillment owner
        fulfillment_owner_email: Email address of the fulfillment owner
        objective_description: Description of the campaign objectives
        placement_data: JSON string containing placement information with COMPLETE targeting data structure
        base_folder_id: Google Drive folder ID where campaign folder will be created (optional, uses env var if not provided)
        sheet_template_id: Google Sheets template ID to copy (optional, uses env var if not provided)
        pdf_template_id: Google Docs template ID for PDF generation (optional, uses env var if not provided)

    CRITICAL: For Media Plan table to populate correctly, placement_data MUST include targeting configuration:

    PLACEMENT DATA STRUCTURE (JSON string):
    [
        {
            "name": "Social Media Campaign",
            "destination": "Instagram",
            "start_date": "2024-06-01",
            "end_date": "2024-08-31",
            "metrics": {
                "impressions": 500000,
                "clicks": 25000
            },
            "bid_rate": {
                "cpm": 2.50,
                "cpc": 0.75
            },
            "budget": {
                "amount": 100000.00
            },
            "targeting": {
                "age_range": "18-34",
                "gender": "Male, Female",
                "income_level": "Middle Income",
                "location": "United States, Canada",
                "interests": "Technology, Gaming",
                "behavioral_data": "Tech Enthusiasts, Early Adopters"
            }
        }
    ]

    EXAMPLES:
    Example: create_insertion_order("IO-123456", "Summer Campaign 2024", "Example Brand", "John Smith", "john@company.com", "Launch summer product line", '[{"name": "Social Media", "destination": "Instagram", "start_date": "2024-06-01", "end_date": "2024-08-31", "metrics": {"impressions": 500000, "clicks": 25000}, "bid_rate": {"cpm": 2.50, "cpc": 0.75}, "budget": {"amount": 100000.00}, "targeting": {"age_range": "18-24", "gender": "Male, Female", "income_level": "Middle Income", "location": "United States", "interests": "Technology", "behavioral_data": "Tech Enthusiasts"}}]')
    """
    logger = logging.getLogger(__name__)

    try:
        # Get credentials
        credentials = _get_google_credentials()
        if not credentials:
            return "Error: Google OAuth credentials not found. Please ensure token.pickle file exists and contains valid credentials."

        # Build Google services
        drive_service = build("drive", "v3", credentials=credentials)
        sheets_service = build("sheets", "v4", credentials=credentials)
        docs_service = build("docs", "v1", credentials=credentials)

        # Get configuration from environment variables or use provided values
        base_folder = base_folder_id or os.getenv("BASE_GOOGLE_DRIVE_FOLDER_ID")
        sheet_template = sheet_template_id or os.getenv("GOOGLE_SHEET_TEMPLATE_ID")
        pdf_template = pdf_template_id or os.getenv("PDF_GENERATION_TEMPLATE_ID")

        if not base_folder:
            return "Error: BASE_GOOGLE_DRIVE_FOLDER_ID not configured. Please set environment variable or provide base_folder_id parameter."
        if not sheet_template:
            return "Error: GOOGLE_SHEET_TEMPLATE_ID not configured. Please set environment variable or provide sheet_template_id parameter."
        if not pdf_template:
            return "Error: PDF_GENERATION_TEMPLATE_ID not configured. Please set environment variable or provide pdf_template_id parameter."

        # Parse placement data - FIX: Handle array of placements
        try:
            placement_list = (
                json.loads(placement_data)
                if isinstance(placement_data, str)
                else placement_data
            )
            if not isinstance(placement_list, list):
                return (
                    "Error: placement_data must be a JSON array of placement objects."
                )
        except json.JSONDecodeError:
            return "Error: Invalid placement_data JSON format."

        # Create campaign folder
        folder_name = f"{campaign_name}_{datetime.now().strftime('%Y%m%d')}"
        campaign_folder = _create_google_drive_folder(
            drive_service, folder_name, base_folder
        )

        # Create PDF subfolder
        pdf_folder = _create_google_drive_folder(
            drive_service, "PDF Files", campaign_folder["id"]
        )

        # Share folders with stakeholders
        stakeholder_emails = [
            customer_approver_email,
            sales_owner_email,
            fulfillment_owner_email,
        ]
        _share_folder_with_users(
            drive_service, campaign_folder["id"], stakeholder_emails
        )

        # Prepare data for sheet (use first placement for sheet data)
        first_placement = placement_list[0] if placement_list else {}
        sheet_data = {
            "order_number": order_number,
            "brand": brand,
            "campaign_name": campaign_name,
            "customer_approver": customer_approver,
            "customer_approver_email": customer_approver_email,
            "sales_owner": sales_owner,
            "sales_owner_email": sales_owner_email,
            "fulfillment_owner": fulfillment_owner,
            "fulfillment_owner_email": fulfillment_owner_email,
            "objective_description": objective_description,
            "placement_name": first_placement.get("name", ""),
            "placement_destination": first_placement.get("destination", ""),
            "start_date": first_placement.get("start_date", ""),
            "end_date": first_placement.get("end_date", ""),
        }

        # Create Google Sheet from template
        sheet_result = _create_sheet_from_template(
            drive_service,
            sheets_service,
            campaign_folder["id"],
            f"Order_{order_number}",
            sheet_template,
            sheet_data,
        )

        # NEW: Prepare Media Plan table data and PDF variables with proper targeting info
        media_plan_table_rows = []
        placement_details = []
        total_impressions = 0
        total_clicks = 0
        total_budget = 0

        for i, placement_info in enumerate(placement_list, 1):
            # Extract placement data
            name = placement_info.get("name", f"Placement {i}")
            destination = placement_info.get("destination", "")
            start_date = placement_info.get("start_date", "")
            end_date = placement_info.get("end_date", "")

            # Extract metrics
            metrics = placement_info.get("metrics", {})
            impressions = metrics.get("impressions", 0)
            clicks = metrics.get("clicks", 0)

            # Extract bid rates
            bid_rate = placement_info.get("bid_rate", {})
            cpm = bid_rate.get("cpm", 0.0)
            cpc = bid_rate.get("cpc", 0.0)

            # Extract budget
            budget = placement_info.get("budget", {})
            amount = budget.get("amount", 0.0)

            # Add to totals
            total_impressions += impressions
            total_clicks += clicks
            total_budget += amount

            # Extract targeting information - FIX: Handle targeting properly
            targeting_info = _extract_targeting_info_from_placement(placement_info)

            # Create detailed placement description
            placement_detail = f"""
Placement {i}: {name}
  Destination: {destination}
  Duration: {start_date} - {end_date}
  Metrics: {impressions:,} impressions, {clicks:,} clicks
  Bid Rate: ${cpm} CPM
  CPC: ${cpc}
  Budget: ${amount:,.2f}
  Target Audience:
    - Age Range: {targeting_info['age_range']}
    - Gender: {targeting_info['gender']}
    - Income Level: {targeting_info['income_level']}
    - Interests: {targeting_info['interests']}
    - Location: {targeting_info['location']}
    - Behavioral Data: {targeting_info['behavioral_data']}
            """.strip()
            placement_details.append(placement_detail)

            # Create table row for media plan table
            targeting_summary = f"{targeting_info['age_range']}, {targeting_info['gender']}, {targeting_info['income_level']}, {targeting_info['location']}, {targeting_info['interests']}, {targeting_info['behavioral_data']}"

            table_row = [
                f"${amount:,.2f}",  # budget
                start_date,  # start date
                end_date,  # end date
                name,  # placement name
                destination,  # placement destination
                targeting_summary,  # targeting
                objective_description,  # objective description
                f"{impressions:,}",  # target impressions
                f"{clicks:,}",  # target clicks
                f"${cpm}",  # cpm
                f"${cpc}",  # cpc
            ]
            media_plan_table_rows.append(table_row)

        # Get overall date range
        start_dates = [
            p.get("start_date", "") for p in placement_list if p.get("start_date")
        ]
        end_dates = [p.get("end_date", "") for p in placement_list if p.get("end_date")]
        earliest_start = min(start_dates) if start_dates else ""
        latest_end = max(end_dates) if end_dates else ""

        # Create media plan table data structure
        media_plan_table = {
            "headers": [
                "Budget",
                "Start Date",
                "End Date",
                "Placement Name",
                "Placement Destination",
                "Targeting",
                "Objective Description",
                "Target Impressions",
                "Target Clicks",
                "CPM",
                "CPC",
            ],
            "rows": media_plan_table_rows,
        }

        # Prepare enhanced PDF template variables with Media Plan table
        pdf_variables = {
            "order_number": order_number,
            "brand": brand,
            "campaign_name": campaign_name,
            "customer_approver": customer_approver,
            "customer_approver_email": customer_approver_email,
            "sales_owner": sales_owner,
            "sales_owner_email": sales_owner_email,
            "fulfillment_owner": fulfillment_owner,
            "fulfillment_owner_email": fulfillment_owner_email,
            "start_date": earliest_start,
            "end_date": latest_end,
            "placement_details": "\n\n".join(placement_details),
            "media_plan_table": media_plan_table,  # This is the key addition!
            "impressions": str(total_impressions),
            "clicks": str(total_clicks),
            "cpm": "Multiple CPM rates (see placement details)",
            "cpc": "Multiple CPC rates (see placement details)",
            "budget_amount": str(total_budget),
            "age_range": "Multiple (see placement details)",
            "gender": "Multiple (see placement details)",
            "income_level": "Multiple (see placement details)",
            "interests": "Multiple (see placement details)",
            "location": "Multiple (see placement details)",
            "audience_segments": "Multiple (see placement details)",
            "device_targeting": "All Devices",
            "objective_description": objective_description,
            "generation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        # Generate PDF with Media Plan table support
        pdf_result = _generate_pdf_with_media_plan_table(
            drive_service,
            docs_service,
            pdf_template,
            pdf_folder["id"],
            f"{order_number}_v0",
            pdf_variables,
        )

        return (
            f"✅ Insertion order created successfully!\n\n"
            f"📁 Campaign Folder: {campaign_folder['link']}\n"
            f"📊 Google Sheet: {sheet_result['sheet_link']}\n"
            f"📄 PDF Document: {pdf_result['pdf_link']}\n\n"
            f"Order Number: {order_number}\n"
            f"Campaign: {campaign_name}\n"
            f"All stakeholders have been granted access to the resources."
        )

    except Exception as e:
        logger.error(f"Error creating insertion order: {str(e)}")
        return f"❌ Error creating insertion order: {str(e)}"


def _connect_to_salesforce():
    """Connect to Salesforce using simple-salesforce library"""
    try:
        from simple_salesforce import Salesforce

        # Get Salesforce credentials from environment
        username = os.getenv("SALESFORCE_USERNAME")
        password = os.getenv("SALESFORCE_PASSWORD")
        security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        domain = os.getenv(
            "SALESFORCE_DOMAIN", "test"
        )  # test for sandbox, login for production

        if not all([username, password, security_token]):
            raise Exception(
                "Missing Salesforce credentials. Please set SALESFORCE_USERNAME, SALESFORCE_PASSWORD, and SALESFORCE_SECURITY_TOKEN environment variables."
            )

        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

        return sf
    except ImportError:
        raise Exception(
            "simple-salesforce library not installed. Please install it with: pip install simple-salesforce"
        )
    except Exception as e:
        raise Exception(f"Failed to connect to Salesforce: {str(e)}")


def _create_salesforce_insertion_order_direct(
    sf, order_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create insertion order record directly in Salesforce (replicating connector service logic)"""
    try:
        # Prepare the insertion order record data - using only core fields that should exist
        sf_data = {
            "Name": f"{order_data['Brand']} - {order_data['CampaignName']}",
            "Order_Number__c": order_data["OrderNo"],
            "Brand__c": order_data["Brand"],
            "Campaign_Name__c": order_data["CampaignName"],
            "Customer_Approver__c": order_data["CustomerApprover"],
            "Customer_Approver_Email__c": order_data["CustomerApproverEmail"],
            "Sales_Owner__c": order_data["SalesOwner"],
            "Sales_Owner_Email__c": order_data["SalesOwnerEmail"],
            "Fulfillment_Owner__c": order_data["FulfillmentOwner"],
            "Fulfillment_Owner_Email__c": order_data["FulfillmentOwnerEmail"],
            "Objective_Description__c": order_data["ObjectiveDetails"]["Description"],
            "Status__c": "Draft",
        }

        # Add lookup fields - only if valid Salesforce IDs and accessible
        # Try to add Account lookup, but continue if it fails due to permissions
        if order_data.get("account_id") and _is_valid_salesforce_id(
            order_data["account_id"]
        ):
            try:
                # Test if we can access this account first
                sf.Account.get(order_data["account_id"])
                sf_data["Account__c"] = order_data["account_id"]
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Cannot access Account {order_data['account_id']}: {str(e)}"
                )
                # Continue without the Account lookup

        # Try to add Opportunity lookup, but continue if it fails due to permissions
        if order_data.get("opportunity_id") and _is_valid_salesforce_id(
            order_data["opportunity_id"]
        ):
            try:
                # Test if we can access this opportunity first
                sf.Opportunity.get(order_data["opportunity_id"])
                sf_data["Opportunity__c"] = order_data["opportunity_id"]
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Cannot access Opportunity {order_data['opportunity_id']}: {str(e)}"
                )
                # Continue without the Opportunity lookup

        # Add PDF link if available
        if order_data.get("PDF_View_Link_c"):
            sf_data["PDF_View_Link__c"] = order_data["PDF_View_Link_c"]

        # Create the main insertion order record
        result = sf.Insertion_Order__c.create(sf_data)
        io_id = result["id"]

        # Create placement records for each placement (replicating connector service logic)
        for placement in order_data.get("Placement", []):
            _create_placement_record_direct(sf, io_id, placement)

        return {
            "id": io_id,
            "success": result["success"],
            "message": "Insertion order created successfully in Salesforce",
        }

    except Exception as e:
        raise Exception(f"Failed to create Salesforce insertion order: {str(e)}")


def _create_placement_record_direct(
    sf, insertion_order_id: str, placement_data: Dict[str, Any]
):
    """Create placement record linked to insertion order (replicating connector service logic)"""
    try:
        placement_record = {
            "Name": placement_data.get("Name", "Placement"),
            "Insertion_Order__c": insertion_order_id,
            "Destination__c": placement_data.get("Destination"),
            "Start_Date__c": placement_data.get("StartDate"),
            "End_Date__c": placement_data.get("EndDate"),
        }

        # Add metrics if available
        if placement_data.get("Metrics"):
            metrics = placement_data["Metrics"]
            if metrics.get("Impressions"):
                placement_record["Impressions__c"] = metrics["Impressions"]
            if metrics.get("Clicks"):
                placement_record["Clicks__c"] = metrics["Clicks"]

        # Add budget if available
        if placement_data.get("Budget") and placement_data["Budget"].get("Amount"):
            placement_record["Budget_Amount__c"] = placement_data["Budget"]["Amount"]

        # Add bid rates if available
        if placement_data.get("BidRate"):
            bid_rate = placement_data["BidRate"]
            if bid_rate.get("CPM"):
                placement_record["CPM__c"] = bid_rate["CPM"]
            if bid_rate.get("CPC"):
                placement_record["CPC__c"] = bid_rate["CPC"]

        # Add targeting configuration if available
        if placement_data.get("targeting"):
            targeting = placement_data["targeting"]
            if targeting.get("age_range"):
                placement_record["target_audience_age_range__c"] = targeting["age_range"]
            if targeting.get("gender"):
                placement_record["target_audience_gender__c"] = targeting["gender"]
            if targeting.get("income_level"):
                placement_record["target_audience_income_level__c"] = targeting["income_level"]
            if targeting.get("location"):
                placement_record["target_audience_location__c"] = targeting["location"]
            if targeting.get("interests"):
                placement_record["target_audience_interests__c"] = targeting["interests"]
            if targeting.get("behavioral_data"):
                placement_record["target_audience_behavioral_data__c"] = ", ".join(
                    targeting["behavioral_data"]
                )

        # Create the placement record
        result = sf.Placement__c.create(placement_record)
        return result

    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Failed to create placement record: {str(e)}"
        )
        # Don't fail the entire operation if placement creation fails
        return None


def _is_valid_salesforce_id(sf_id: str) -> bool:
    """Check if a string is a valid Salesforce ID format"""
    if not sf_id or not isinstance(sf_id, str):
        return False
    # Salesforce IDs are 15 or 18 characters long and alphanumeric
    return len(sf_id) in [15, 18] and sf_id.isalnum()


@function_schema
def get_salesforce_accounts() -> str:
    """
    GET SALESFORCE ACCOUNTS

    Retrieves a list of all Salesforce Accounts for dropdown population or selection.
    This tool uses direct Salesforce API calls to fetch account data.

    Returns:
        A formatted string containing account information including:
        - Account ID
        - Account Name
        - Total number of accounts found

    EXAMPLES:
    Example: get_salesforce_accounts()
    """
    logger = logging.getLogger(__name__)

    try:
        # Connect to Salesforce directly
        logger.info("Connecting to Salesforce to retrieve accounts")
        sf = _connect_to_salesforce()

        # Query for accounts
        query = "SELECT Id, Name, Type, Industry FROM Account ORDER BY Name LIMIT 1000"
        result = sf.query(query)

        accounts = result["records"]
        logger.info(f"Retrieved {len(accounts)} Salesforce accounts")

        if not accounts:
            return "No Salesforce accounts found."

        # Format the results for display
        response = f"✅ Found {len(accounts)} Salesforce Accounts:\n\n"

        for i, account in enumerate(accounts, 1):
            account_id = account.get("Id", "N/A")
            account_name = account.get("Name", "N/A")
            account_type = account.get("Type", "N/A")
            industry = account.get("Industry", "N/A")

            response += f"{i:3d}. {account_name}\n"
            response += f"     ID: {account_id}\n"
            response += f"     Type: {account_type}\n"
            response += f"     Industry: {industry}\n\n"

            # Limit display to first 20 accounts to avoid overwhelming output
            if i >= 20:
                remaining = len(accounts) - 20
                if remaining > 0:
                    response += f"... and {remaining} more accounts\n\n"
                break

        response += f"📊 Total Accounts: {len(accounts)}\n"
        response += f"🔗 Use Account IDs with other Salesforce tools"

        return response

    except Exception as e:
        logger.error(f"Error retrieving Salesforce accounts: {str(e)}")
        return f"❌ Error retrieving Salesforce accounts: {str(e)}"


@function_schema
def get_salesforce_opportunities() -> str:
    """
    GET SALESFORCE OPPORTUNITIES

    Retrieves a list of all Salesforce Opportunities with key details.
    This tool uses direct Salesforce API calls to fetch opportunity data.

    Returns:
        A formatted string containing opportunity information including:
        - Opportunity ID
        - Opportunity Name
        - Stage Name
        - Amount
        - Close Date
        - Associated Account

    EXAMPLES:
    Example: get_salesforce_opportunities()
    """
    logger = logging.getLogger(__name__)

    try:
        # Connect to Salesforce directly
        logger.info("Connecting to Salesforce to retrieve opportunities")
        sf = _connect_to_salesforce()

        # Query for opportunities with account information
        query = """SELECT Id, Name, StageName, Amount, CloseDate, Type, Description,
                          AccountId, Account.Name, Account__c, Account__r.Name
                   FROM Opportunity
                   ORDER BY CloseDate DESC, Name
                   LIMIT 1000"""
        result = sf.query(query)

        opportunities = result["records"]
        logger.info(f"Retrieved {len(opportunities)} Salesforce opportunities")

        if not opportunities:
            return "No Salesforce opportunities found."

        # Format the results for display
        response = f"✅ Found {len(opportunities)} Salesforce Opportunities:\n\n"

        for i, opp in enumerate(opportunities, 1):
            opp_id = opp.get("Id", "N/A")
            opp_name = opp.get("Name", "N/A")
            stage = opp.get("StageName", "N/A")
            amount = opp.get("Amount", 0)
            close_date = opp.get("CloseDate", "N/A")
            opp_type = opp.get("Type", "N/A")

            # Get account name (try different fields)
            account_name = "N/A"
            if opp.get("Account") and opp["Account"].get("Name"):
                account_name = opp["Account"]["Name"]
            elif opp.get("Account__r") and opp["Account__r"].get("Name"):
                account_name = opp["Account__r"]["Name"]

            # Format amount
            amount_str = f"${amount:,.2f}" if amount else "N/A"

            response += f"{i:3d}. {opp_name}\n"
            response += f"     ID: {opp_id}\n"
            response += f"     Account: {account_name}\n"
            response += f"     Stage: {stage}\n"
            response += f"     Amount: {amount_str}\n"
            response += f"     Close Date: {close_date}\n"
            response += f"     Type: {opp_type}\n\n"

            # Limit display to first 15 opportunities to avoid overwhelming output
            if i >= 15:
                remaining = len(opportunities) - 15
                if remaining > 0:
                    response += f"... and {remaining} more opportunities\n\n"
                break

        response += f"📊 Total Opportunities: {len(opportunities)}\n"
        response += f"🔗 Use Opportunity IDs with other Salesforce tools"

        return response

    except Exception as e:
        logger.error(f"Error retrieving Salesforce opportunities: {str(e)}")
        return f"❌ Error retrieving Salesforce opportunities: {str(e)}"


@function_schema
def get_salesforce_opportunities_by_account(account_id: str) -> str:
    """
    GET SALESFORCE OPPORTUNITIES BY ACCOUNT

    Retrieves Salesforce Opportunities associated with a specific Account.
    This tool uses direct Salesforce API calls to fetch filtered opportunity data.

    Args:
        account_id: The Salesforce Account ID to filter opportunities by

    Returns:
        A formatted string containing opportunity information for the specified account including:
        - Opportunity ID
        - Opportunity Name
        - Stage Name
        - Amount
        - Close Date
        - Account Name

    EXAMPLES:
    Example: get_salesforce_opportunities_by_account("001XX000003DHP0YAO")
    """
    logger = logging.getLogger(__name__)

    try:
        # Validate account ID format
        if not _is_valid_salesforce_id(account_id):
            return f"❌ Invalid Salesforce Account ID format: {account_id}. Expected 15 or 18 character alphanumeric ID."

        # Connect to Salesforce directly
        logger.info(
            f"Connecting to Salesforce to retrieve opportunities for account: {account_id}"
        )
        sf = _connect_to_salesforce()

        # First, try to get the account name to verify it exists
        account_name = "Unknown Account"
        try:
            account_result = sf.Account.get(account_id)
            account_name = account_result.get("Name", "Unknown Account")
        except Exception as account_error:
            logger.warning(
                f"Could not retrieve account details for {account_id}: {str(account_error)}"
            )

        # Query for opportunities using both standard AccountId and custom Account__c lookup field
        query = f"""SELECT Id, Name, StageName, Amount, CloseDate, Type, Description,
                           AccountId, Account.Name, Account__c, Account__r.Name
                    FROM Opportunity
                    WHERE AccountId = '{account_id}' OR Account__c = '{account_id}'
                    ORDER BY CloseDate DESC, Name
                    LIMIT 1000"""
        result = sf.query(query)

        opportunities = result["records"]
        logger.info(
            f"Retrieved {len(opportunities)} Salesforce opportunities for account: {account_id}"
        )

        if not opportunities:
            return (
                f"No opportunities found for Account: {account_name} (ID: {account_id})"
            )

        # Format the results for display
        response = (
            f"✅ Found {len(opportunities)} Opportunities for Account: {account_name}\n"
        )
        response += f"🏢 Account ID: {account_id}\n\n"

        total_amount = 0
        for i, opp in enumerate(opportunities, 1):
            opp_id = opp.get("Id", "N/A")
            opp_name = opp.get("Name", "N/A")
            stage = opp.get("StageName", "N/A")
            amount = opp.get("Amount", 0)
            close_date = opp.get("CloseDate", "N/A")
            opp_type = opp.get("Type", "N/A")

            # Add to total amount if numeric
            if isinstance(amount, (int, float)) and amount > 0:
                total_amount += amount

            # Format amount
            amount_str = f"${amount:,.2f}" if amount else "N/A"

            response += f"{i:3d}. {opp_name}\n"
            response += f"     ID: {opp_id}\n"
            response += f"     Stage: {stage}\n"
            response += f"     Amount: {amount_str}\n"
            response += f"     Close Date: {close_date}\n"
            response += f"     Type: {opp_type}\n\n"

        # Add summary information
        response += f"📊 Summary:\n"
        response += f"   • Total Opportunities: {len(opportunities)}\n"
        response += f"   • Total Pipeline Value: ${total_amount:,.2f}\n"
        response += f"   • Account: {account_name}\n\n"
        response += f"🔗 Use Opportunity IDs with other Salesforce tools"

        return response

    except Exception as e:
        logger.error(
            f"Error retrieving opportunities for account {account_id}: {str(e)}"
        )
        return f"❌ Error retrieving opportunities for account {account_id}: {str(e)}"


@function_schema
def create_salesforce_insertion_order(
    order_number: str,
    campaign_name: str,
    brand: str,
    customer_approver: str,
    customer_approver_email: str,
    sales_owner: str,
    sales_owner_email: str,
    fulfillment_owner: str,
    fulfillment_owner_email: str,
    objective_description: str,
    placement_data: str,
    salesforce_account: str,
    salesforce_opportunity_id: str,
    salesforce_base_url: Optional[str] = None,
    base_folder_id: Optional[str] = None,
    pdf_template_id: Optional[str] = None,
) -> str:
    """
    CREATE INSERTION ORDER IN SALESFORCE (DIRECT API)

    Creates a complete insertion order in Salesforce with PDF documentation in Google Drive.
    This tool uses direct Salesforce API calls (no external connector service required) and automates:
    - Creating a PDF document in Google Drive with Media Plan table
    - Creating an insertion order record directly in Salesforce via API
    - Creating placement records with targeting and budget data
    - Linking the PDF to the Salesforce record
    - Returning URLs for both Salesforce record and PDF document

    Args:
        order_number: The insertion order number (e.g., "IO-340371-3439")
        campaign_name: Name of the marketing campaign
        brand: Brand name for the campaign
        customer_approver: Name of the customer approver
        customer_approver_email: Email address of the customer approver
        sales_owner: Name of the sales owner
        sales_owner_email: Email address of the sales owner
        fulfillment_owner: Name of the fulfillment owner
        fulfillment_owner_email: Email address of the fulfillment owner
        objective_description: Description of the campaign objectives
        placement_data: JSON string containing placement information with COMPLETE targeting data structure
        salesforce_account: Salesforce Account ID for the insertion order
        salesforce_opportunity_id: Salesforce Opportunity ID for the insertion order
        salesforce_base_url: Base URL for Salesforce Lightning (optional, uses env var if not provided)
        base_folder_id: Google Drive folder ID where PDF will be created (optional, uses env var if not provided)
        pdf_template_id: Google Docs template ID for PDF generation (optional, uses env var if not provided)

    CRITICAL: For Media Plan table to populate correctly, placement_data MUST include targeting configuration:

    PLACEMENT DATA STRUCTURE (JSON string):
    [
        {
            "name": "Social Media Campaign",
            "destination": "Instagram",
            "start_date": "2024-06-01",
            "end_date": "2024-08-31",
            "metrics": {
                "impressions": 500000,
                "clicks": 25000
            },
            "bid_rate": {
                "cpm": 2.50,
                "cpc": 0.75
            },
            "budget": {
                "amount": 100000.00
            },
            "targeting": {
                "age_range": "18-34",
                "gender": "Male, Female",
                "income_level": "Middle Income",
                "location": "United States, Canada",
                "interests": "Technology, Gaming",
                "behavioral_data": "Tech Enthusiasts, Early Adopters"
            }
        }
    ]

    EXAMPLES:
    Example: create_salesforce_insertion_order("IO-123456", "Summer Campaign 2024", "Example Brand", "John Smith", "john@company.com", "Launch summer product line", '[{"name": "Social Media", "destination": "Instagram", "start_date": "2024-06-01", "end_date": "2024-08-31", "metrics": {"impressions": 500000, "clicks": 25000}, "bid_rate": {"cpm": 2.50, "cpc": 0.75}, "budget": {"amount": 100000.00}, "targeting": {"age_range": "18-24", "gender": "Male, Female", "income_level": "Middle Income", "location": "United States", "interests": "Technology", "behavioral_data": "Tech Enthusiasts"}}]', "001XX000003DHP0", "006XX000004TMi2")
    """
    logger = logging.getLogger(__name__)

    try:
        # Get credentials for Google Drive PDF generation
        credentials = _get_google_credentials()
        if not credentials:
            return "Error: Google OAuth credentials not found. Please ensure token.pickle file exists and contains valid credentials."

        # Build Google services
        drive_service = build("drive", "v3", credentials=credentials)
        docs_service = build("docs", "v1", credentials=credentials)

        # Get configuration from environment variables or use provided values
        base_folder = base_folder_id or os.getenv("BASE_GOOGLE_DRIVE_FOLDER_ID")
        pdf_template = pdf_template_id or os.getenv("PDF_GENERATION_TEMPLATE_ID")
        sf_base_url = salesforce_base_url or os.getenv(
            "SALESFORCE_BASE_URL", "https://flow-business-5971.lightning.force.com"
        )

        if not base_folder:
            return "Error: BASE_GOOGLE_DRIVE_FOLDER_ID not configured. Please set environment variable or provide base_folder_id parameter."
        if not pdf_template:
            return "Error: PDF_GENERATION_TEMPLATE_ID not configured. Please set environment variable or provide pdf_template_id parameter."

        # Parse placement data - FIX: Handle array of placements
        try:
            placement_list = (
                json.loads(placement_data)
                if isinstance(placement_data, str)
                else placement_data
            )
            if not isinstance(placement_list, list):
                return (
                    "Error: placement_data must be a JSON array of placement objects."
                )
        except json.JSONDecodeError:
            return "Error: Invalid placement_data JSON format."

        # Step 1: Create PDF documentation in Google Drive
        logger.info("Creating Salesforce PDF documentation")

        # Create campaign folder for Salesforce
        folder_name = f"{campaign_name}_{datetime.now().strftime('%Y%m%d')}_Salesforce"
        campaign_folder = _create_google_drive_folder(
            drive_service, folder_name, base_folder
        )

        # Create PDF subfolder
        pdf_folder = _create_google_drive_folder(
            drive_service, "PDF Files", campaign_folder["id"]
        )

        # Share folders with stakeholders
        stakeholder_emails = [
            customer_approver_email,
            sales_owner_email,
            fulfillment_owner_email,
        ]
        _share_folder_with_users(
            drive_service, campaign_folder["id"], stakeholder_emails
        )

        # NEW: Prepare Media Plan table data and PDF variables with proper targeting info
        media_plan_table_rows = []
        placement_details = []
        total_impressions = 0
        total_clicks = 0
        total_budget = 0

        for i, placement_info in enumerate(placement_list, 1):
            # Extract placement data
            name = placement_info.get("name", f"Placement {i}")
            destination = placement_info.get("destination", "")
            start_date = placement_info.get("start_date", "")
            end_date = placement_info.get("end_date", "")

            # Extract metrics
            metrics = placement_info.get("metrics", {})
            impressions = metrics.get("impressions", 0)
            clicks = metrics.get("clicks", 0)

            # Extract bid rates
            bid_rate = placement_info.get("bid_rate", {})
            cpm = bid_rate.get("cpm", 0.0)
            cpc = bid_rate.get("cpc", 0.0)

            # Extract budget
            budget = placement_info.get("budget", {})
            amount = budget.get("amount", 0.0)

            # Add to totals
            total_impressions += impressions
            total_clicks += clicks
            total_budget += amount

            # Extract targeting information
            targeting_info = _extract_targeting_info_from_placement(placement_info)

            # Create detailed placement description
            placement_detail = f"""
Placement {i}: {name}
  Destination: {destination}
  Duration: {start_date} - {end_date}
  Metrics: {impressions:,} impressions, {clicks:,} clicks
  Bid Rate: ${cpm} CPM
  CPC: ${cpc}
  Budget: ${amount:,.2f}
  Target Audience:
    - Age Range: {targeting_info['age_range']}
    - Gender: {targeting_info['gender']}
    - Income Level: {targeting_info['income_level']}
    - Interests: {targeting_info['interests']}
    - Location: {targeting_info['location']}
    - Behavioral Data: {targeting_info['behavioral_data']}
            """.strip()
            placement_details.append(placement_detail)

            # Create table row for media plan table
            targeting_summary = f"{targeting_info['age_range']}, {targeting_info['gender']}, {targeting_info['income_level']}, {targeting_info['location']}, {targeting_info['interests']}, {targeting_info['behavioral_data']}"

            table_row = [
                f"${amount:,.2f}",  # budget
                start_date,  # start date
                end_date,  # end date
                name,  # placement name
                destination,  # placement destination
                targeting_summary,  # targeting
                objective_description,  # objective description
                f"{impressions:,}",  # target impressions
                f"{clicks:,}",  # target clicks
                f"${cpm}",  # cpm
                f"${cpc}",  # cpc
            ]
            media_plan_table_rows.append(table_row)

        # Get overall date range
        start_dates = [
            p.get("start_date", "") for p in placement_list if p.get("start_date")
        ]
        end_dates = [p.get("end_date", "") for p in placement_list if p.get("end_date")]
        earliest_start = min(start_dates) if start_dates else ""
        latest_end = max(end_dates) if end_dates else ""

        # Create media plan table data structure
        media_plan_table = {
            "headers": [
                "Budget",
                "Start Date",
                "End Date",
                "Placement Name",
                "Placement Destination",
                "Targeting",
                "Objective Description",
                "Target Impressions",
                "Target Clicks",
                "CPM",
                "CPC",
            ],
            "rows": media_plan_table_rows,
        }

        # Prepare enhanced PDF template variables with Media Plan table
        pdf_variables = {
            "order_number": order_number,
            "brand": brand,
            "campaign_name": campaign_name,
            "customer_approver": customer_approver,
            "customer_approver_email": customer_approver_email,
            "sales_owner": sales_owner,
            "sales_owner_email": sales_owner_email,
            "fulfillment_owner": fulfillment_owner,
            "fulfillment_owner_email": fulfillment_owner_email,
            "start_date": earliest_start,
            "end_date": latest_end,
            "placement_details": "\n\n".join(placement_details),
            "media_plan_table": media_plan_table,  # This is the key addition!
            "impressions": str(total_impressions),
            "clicks": str(total_clicks),
            "cpm": "Multiple CPM rates (see placement details)",
            "cpc": "Multiple CPC rates (see placement details)",
            "budget_amount": str(total_budget),
            "age_range": "Multiple (see placement details)",
            "gender": "Multiple (see placement details)",
            "income_level": "Multiple (see placement details)",
            "interests": "Multiple (see placement details)",
            "location": "Multiple (see placement details)",
            "audience_segments": "Multiple (see placement details)",
            "device_targeting": "All Devices",
            "objective_description": objective_description,
            "generation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        # Generate PDF with Media Plan table support
        pdf_result = _generate_pdf_with_media_plan_table(
            drive_service,
            docs_service,
            pdf_template,
            pdf_folder["id"],
            f"{order_number}_Salesforce_v0",
            pdf_variables,
        )

        logger.info(f"PDF created successfully: {pdf_result['pdf_file_id']}")

        # Step 2: Prepare Salesforce data with PDF link
        salesforce_data = {
            "account_id": salesforce_account,
            "opportunity_id": salesforce_opportunity_id,
            "OrderNo": order_number,
            "Brand": brand,
            "CampaignName": campaign_name,
            "CustomerApprover": customer_approver,
            "CustomerApproverEmail": customer_approver_email,
            "SalesOwner": sales_owner,
            "SalesOwnerEmail": sales_owner_email,
            "FulfillmentOwner": fulfillment_owner,
            "FulfillmentOwnerEmail": fulfillment_owner_email,
            "ObjectiveDetails": {"Description": objective_description},
            "Placement": placement_list,  # Use the full placement list
            "PDF_View_Link_c": pdf_result["pdf_link"],  # Include the PDF link
        }

        # Step 3: Connect to Salesforce and create insertion order directly
        logger.info("Connecting to Salesforce and creating insertion order record")
        try:
            sf = _connect_to_salesforce()
            salesforce_response = _create_salesforce_insertion_order_direct(
                sf, salesforce_data
            )
        except Exception as sf_error:
            logger.error(f"Salesforce integration error: {str(sf_error)}")
            return f"❌ Error creating Salesforce insertion order: {str(sf_error)}"

        logger.info(f"Salesforce insertion order created: {salesforce_response}")

        # Step 4: Generate Salesforce Lightning URL
        salesforce_record_id = salesforce_response.get("id", "")
        salesforce_record_url = (
            f"{sf_base_url}/lightning/r/Insertion_Order__c/{salesforce_record_id}/view"
        )

        # Prepare success response
        return (
            f"✅ Salesforce insertion order created successfully!\n\n"
            f"🏢 Salesforce Record: {salesforce_record_url}\n"
            f"📄 PDF Document: {pdf_result['pdf_link']}\n"
            f"📁 Campaign Folder: {campaign_folder['link']}\n\n"
            f"Order Number: {order_number}\n"
            f"Campaign: {campaign_name}\n"
            f"Salesforce Account: {salesforce_account}\n"
            f"Salesforce Opportunity: {salesforce_opportunity_id}\n"
            f"Record ID: {salesforce_record_id}"
        )

    except Exception as e:
        logger.error(f"Error creating Salesforce insertion order: {str(e)}")
        return f"❌ Error creating Salesforce insertion order: {str(e)}"


@function_schema
def query_retriever(query: str, machine_types: Optional[List[str]] = None) -> list:
    """
    RETRIEVER TOOL

    Use this tool to query the Toshiba knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    If the user enters a machine type, add it to the machine_types list. For example, if the user asks "What is the part number for the Motorized Controller on the 6800?", add "6800" to the machine_types list.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="What is TAL"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"

    Example: query="diagnostic code X is 0 Y is 2"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".

    DO NOT ADD MACHINE TYPES TO THE QUERY. ONLY USE THE MACHINE TYPES LIST.
    FOR EXAMPLE, IF THE USER ASKS "What is the part number for the Motorized Controller on the 6800 System 7?",
    ADD "6800" TO THE MACHINE TYPES LIST.
    AND THEN QUERY WITH "part number for the Motorized Controller System 7"
    NOTICE HOW THE MACHINE NAME "SYSTEM 7" IS INCLUDED IN THE QUERY.

    INCLUDE THE MODEL NUMBER AND NAME IN THE QUERY IF AVAILABLE.
    FOR EXAMPLE, IF THE USER ASKS "SureBase (Machine Type: 4800 Model: 0xx) SLO motor part"
    ADD "4800" TO THE MACHINE TYPES LIST.
    AND THEN QUERY WITH "part number for the Motorized Controller for SureBase model 100".
    NOTICE HOW THE MACHINE NAME "SureBase" IS INCLUDED IN THE QUERY.

    VALID MACHINE TYPES:

    1. 2001
    2. 2011
    3. 4612
    4. 4613
    5. 4614
    6. 4615
    7. 4674
    8. 4683
    9. 4693
    10. 4694
    11. 4695
    12. 4750
    13. 4800
    14. 4810
    15. 4818
    16. 4825
    17. 4828
    18. 4835
    19. 4836
    20. 4838
    21. 4840
    22. 4845
    23. 4846
    24. 4851
    25. 4852
    26. 4855
    27. 4888
    28. 4900
    29. 4901
    30. 4910
    31. 6140
    32. 6183
    33. 6200
    34. 6201
    35. 6225
    36. 6700
    37. 6800
    38. 6900
    39. 7054
    40. 8368
    41. 4610
    42. 4679
    43. 4685
    44. 4698
    45. 4689
    46. 4820
    47. 6145
    48. 6149
    49. 6150
    50. 6160
    51. 6180
    52. 6260
    53. 9338

    If no machine types are provided, query without the machine type.
    """

    def get_response(url, params):
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            print("^"*100)
            print("Response")
            print(response.json())
            print("^" * 100)
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i, segment in enumerate(segments):
                res += "*" * 5 + f"\n\nSegment Begins: " + "\n"  # +"Contextual Header: "
                references = ""
                for j, chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: " + chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"] + f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
                    if "page" in filename:
                        sources.append(f"{filename}" + f" [aws_id: {filename}] score: [{round(segment['score'], 2)}]")
                    else:
                        sources.append(
                            f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}] score: [{round(segment['score'], 2)}]")
            res += "Segment Ends\n" + "-" * 5 + "\n\n"

            return [res, sources]
        except Exception as e:
            print(f"Failed to call retriever: {e}")
            return ["", []]

    url = os.getenv("TGCS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60,
        "machine_types": machine_types,
        "collection_id": "toshiba_demo_4"

    }
    try:
        first_response, sources = get_response(url, params)
        print("-" * 100)
        print("\nGot response")
        print(first_response[:200])
        print(sources)
        print("-" * 100)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["", []]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "machine_types": machine_types
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["", []]
    # print(first_response+second_response)
    # print(sources+second_sources)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    print(res + first_response + second_response)
    return [res + first_response + second_response, sources + second_sources]


@function_schema
def customer_query_retriever(query: str, collection_id: str) -> list:
    """"
    TOSHIBA CUSTOMER DATA RETRIEVER TOOL

    Use this tool to query the Toshiba's Customer knowledge base.
    This tool is only used for customer-specific information.
    List of customers and their collection_ids:
    1. Walgreens: toshiba_walgreens
    2. Kroger: toshiba_kroger (Note that Harris Teeter is also included in this collection)
    3. Sam's Club: toshiba_sams_club
    4. Tractor Supply: toshiba_tractor_supply
    5. Dollar General: toshiba_dollar_general
    6. Wegmans: toshiba_wegmans
    7. Ross: toshiba_ross
    8. Costco: toshiba_costco
    9. Whole Foods: toshiba_whole_foods
    10. BJs: toshiba_bjs
    11. Alex Lee: toshiba_alex_lee
    12. Badger: toshiba_badger
    13. Best Buy: toshiba_best_buy
    14. GNC: toshiba_GNC
    15. Coach: toshiba_coach
    16. QuickChek: toshiba_quickchek
    16. CAM: toshiba_cameras_al
    17. Hudson News: toshiba_hudson_news
    18. IDKIDS: toshiba_idkids

    Use toshiba_demo_4 if the customer retriever fails to return any relevant results

    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"

    Essentially, if the user asks "Walgreens <question>" then the query should be "<question>" and the collection_id should be "toshiba_walgreens"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
        # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i, segment in enumerate(segments):
                res += "*" * 5 + f"\n\nSegment Begins: " + "\n"  # +"Contextual Header: "
                references = ""
                for j, chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: " + chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        # print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res += f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
                    if "page" in filename:
                        sources.append(f"{filename}" + f" [aws_id: {filename}] score: [{round(segment['score'], 2)}]")
                    else:
                        sources.append(
                            f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}] score: [{round(segment['score'], 2)}]")

            res += "Segment Ends\n" + "-" * 5 + "\n\n"

            return [res, sources]
        except Exception as e:
            print(f"Failed to call retriever: {e}")
            return ["", []]

    url = os.getenv("CUSTOMER_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60,
        "collection_id": collection_id
    }
    first_response, sources = ["", []]
    try:
        first_response, sources = get_response(url, params)
        print("-"*100)
        print("\nGot response")
        print(first_response[:200])
        print(sources)
        print("-"*100)
    except Exception as e:
        print(f"Failed to call retriever: {e}")

    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["", []]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    print(res + first_response)
    return [res + first_response, sources]


@function_schema
def sql_database(query: str) -> list:
    """"
    SQL DATABASE TOOL
    Any query that has "SQL: <question>" MUST use this tool.

    Use this tool to query the Toshiba Service Request database.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    query = "What are the SR tickets closed on 2024-11-06 and who resolved them?"
    query = "Which SRs were resolved between 2024-11-05 and 2024-11-07?"
    query = "Which SRs closed in Florida and who handled them?"
    query = "What tickets were handled by Jason Hechler?"
    """
    st_url = os.getenv("SQL_RETRIEVER_URL") + "/query"
    params = {
        "query": query
    }
    try:
        print(st_url)
        print(params)
        response = requests.post(st_url, params=params)
        print(response.json())
        res = response.json()["response"]
        return [res, []]
    except Exception as e:
        print(f"Failed to call SR database: {e}")
        return []

@function_schema
def arlo_api(query:str)->str:
    """
    Use this tool to ask questions to the Arlo customer support agent.
    """
    url = "https://elevaite-arlocb-api.iopex.ai/chat"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "message": query,
        "session_id": "3973740a-404d-4924-9cf4-c71cf9ffd219",
        "user_id": "Jojo",
        "chat_history": [
            {"actor": "user", "content": "Hello"},
            {"actor": "assistant", "content": "How are you"}
        ],
        "enable_web_search": True,
        "fetched_knowledge": ""
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()['response']


tool_store = {
    "add_numbers": add_numbers,
    "weather_forecast": weather_forecast,
    "url_to_markdown": url_to_markdown,
    "web_search": web_search,
    "get_customer_order": get_customer_order,
    "get_customer_location": get_customer_location,
    "add_customer": add_customer,
    "print_to_console": print_to_console,
    "query_retriever2": query_retriever2,
    "media_context_retriever": media_context_retriever,
    "redis_cache_operation": redis_cache_operation,
    "postgres_query": postgres_query,
    "image_generation": image_generation,
    "create_insertion_order": create_insertion_order,
    "create_salesforce_insertion_order": create_salesforce_insertion_order,
    "get_salesforce_accounts": get_salesforce_accounts,
    "get_salesforce_opportunities": get_salesforce_opportunities,
    "get_salesforce_opportunities_by_account": get_salesforce_opportunities_by_account,
    # Backward compatibility aliases for renamed functions
    "qdrant_search": media_context_retriever,  # Alias for backward compatibility
    "query_retriever": query_retriever,
    "customer_query_retriever": customer_query_retriever,
    "sql_database": sql_database,
    "arlo_api": arlo_api,
}


tool_schemas = {
    "add_numbers": add_numbers.openai_schema,
    "weather_forecast": weather_forecast.openai_schema,
    "url_to_markdown": url_to_markdown.openai_schema,
    "web_search": web_search.openai_schema,
    "get_customer_order": get_customer_order.openai_schema,
    "get_customer_location": get_customer_location.openai_schema,
    "add_customer": add_customer.openai_schema,
    "print_to_console": print_to_console.openai_schema,
    "query_retriever2": query_retriever2.openai_schema,
    "media_context_retriever": media_context_retriever.openai_schema,
    "redis_cache_operation": redis_cache_operation.openai_schema,
    "postgres_query": postgres_query.openai_schema,
    "image_generation": image_generation.openai_schema,
    "create_insertion_order": create_insertion_order.openai_schema,
    "create_salesforce_insertion_order": create_salesforce_insertion_order.openai_schema,
    "get_salesforce_accounts": get_salesforce_accounts.openai_schema,
    "get_salesforce_opportunities": get_salesforce_opportunities.openai_schema,
    "get_salesforce_opportunities_by_account": get_salesforce_opportunities_by_account.openai_schema,
    # Backward compatibility aliases for renamed functions
    "qdrant_search": media_context_retriever.openai_schema,  # Alias for backward compatibility
    "query_retriever": query_retriever.openai_schema,
    "customer_query_retriever": customer_query_retriever.openai_schema,
    "sql_database": sql_database.openai_schema,
    "arlo_api": arlo_api.openai_schema,
}
