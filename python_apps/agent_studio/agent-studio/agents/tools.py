import os
import dotenv
import requests
import markdownify
from bs4 import BeautifulSoup
from utils import function_schema
from typing import Optional
from utils import client

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
        order_number = [i["order_number"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id][0]
        return f"The order number for customer ID {customer_id} is {order_number}"
    return f"No order found for customer ID {customer_id}"


@function_schema
def get_customer_location(customer_id: int) -> str:
    """ "
    Returns the location for a given customer ID."""
    if customer_id in [i["customer_id"] for i in EXAMPLE_DATA]:
        location = [i["location"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id][0]
        return f"The location for customer ID {customer_id} is {location}"
    return f"No location found for customer ID {customer_id}"


@function_schema
def add_customer(customer_id: int, order_number: int, location: str) -> str:
    """ "
    Adds a new customer to the database."""
    EXAMPLE_DATA.append({"customer_id": customer_id, "order_number": order_number, "location": location})
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
            markdown_content = markdownify.markdownify(str(content), heading_style="ATX")
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
        raise ValueError("RETRIEVER_URL not found. Please set it in the environment variables.")
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
        res += contextual_header if contextual_header else "No contextual header" + "\n" + "Context: " + "\n"
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
def qdrant_search(query: str, collection_name: str, limit: Optional[int] = 10, filter_params: Optional[str] = None) -> str:
    """
    QDRANT VECTOR SEARCH TOOL

    Use this tool to perform vector similarity search on Qdrant database for media campaigns and creatives.

    Args:
        query: The search query text for semantic similarity search
        collection_name: Name of the Qdrant collection to search (e.g., 'campaigns', 'creatives')
        limit: Maximum number of results to return (default: 10)
        filter_params: Optional JSON string with filter parameters (e.g., '{"brand": "nike", "industry": "Fashion & Retail"}')

    EXAMPLES:
    Example: qdrant_search("high performing fashion campaigns", "campaigns", 5)
    Example: qdrant_search("summer beverage ads", "creatives", 10, '{"season": "summer", "industry": "Food & Beverage"}')
    Example: qdrant_search("Nike campaigns with high CTR", "campaigns", 8, '{"brand": "nike"}')
    """
    # Mock implementation - in real scenario this would connect to Qdrant
    print(f"Searching Qdrant collection '{collection_name}' with query: '{query}'")
    print(f"Limit: {limit}, Filters: {filter_params}")

    # Mock response data
    mock_results = [
        {
            "id": "campaign_001",
            "score": 0.95,
            "payload": {
                "campaign_name": "Summer Fashion Collection 2024",
                "brand": "Nike",
                "industry": "Fashion & Retail",
                "season": "summer",
                "conversion_rate": 0.045,
                "clicks": 15420,
                "impressions": 342000,
                "budget": 25000
            }
        },
        {
            "id": "campaign_002",
            "score": 0.87,
            "payload": {
                "campaign_name": "Holiday Beverage Campaign",
                "brand": "Coca-Cola",
                "industry": "Food & Beverage",
                "season": "winter",
                "conversion_rate": 0.038,
                "clicks": 12800,
                "impressions": 337000,
                "budget": 18000
            }
        }
    ]

    result_text = f"QDRANT SEARCH RESULTS for '{query}':\n\n"
    for i, result in enumerate(mock_results[:limit]):
        result_text += f"Result {i+1} (Score: {result['score']}):\n"
        result_text += f"Campaign: {result['payload']['campaign_name']}\n"
        result_text += f"Brand: {result['payload']['brand']}\n"
        result_text += f"Industry: {result['payload']['industry']}\n"
        result_text += f"Conversion Rate: {result['payload']['conversion_rate']}\n"
        result_text += f"Clicks: {result['payload']['clicks']}\n"
        result_text += f"Budget: ${result['payload']['budget']}\n"
        result_text += "-" * 40 + "\n"

    return result_text


@function_schema
def redis_cache_operation(operation: str, key: str, value: Optional[str] = None, ttl: Optional[int] = None) -> str:
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
            "targeting:config:tech_professionals": '{"age_range": ["25-44"], "interests": ["Technology"]}'
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
        existing_keys = ["campaign:nike:performance", "user:session:12345", "targeting:config:tech_professionals"]
        exists = key in existing_keys
        return f"Key '{key}' {'exists' if exists else 'does not exist'} in Redis"

    elif operation == "keys":
        # Mock pattern matching
        mock_keys = [
            "campaign:nike:performance",
            "campaign:cocacola:metrics",
            "campaign:disney:analytics",
            "user:session:12345",
            "targeting:config:tech_professionals"
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
def postgres_query(query_type: str, table: str, conditions: Optional[str] = None, data: Optional[str] = None, limit: Optional[int] = 10) -> str:
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
        {"id": 1, "name": "Summer Fashion 2024", "brand": "nike", "industry": "Fashion & Retail", "conversion_rate": 0.045, "budget": 25000, "status": "active"},
        {"id": 2, "name": "Holiday Beverages", "brand": "coca-cola", "industry": "Food & Beverage", "conversion_rate": 0.038, "budget": 18000, "status": "completed"},
        {"id": 3, "name": "Tech Innovation", "brand": "apple", "industry": "Technology & Telecommunications", "conversion_rate": 0.052, "budget": 35000, "status": "active"},
        {"id": 4, "name": "Automotive Excellence", "brand": "toyota", "industry": "Automotive", "conversion_rate": 0.041, "budget": 22000, "status": "paused"}
    ]

    mock_users = [
        {"id": 101, "username": "john_doe", "email": "john@example.com", "role": "campaign_manager", "created_at": "2024-01-10"},
        {"id": 102, "username": "jane_smith", "email": "jane@example.com", "role": "analyst", "created_at": "2024-01-12"}
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
        return f"Successfully inserted new record into '{table}' table with data: {data}"

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
def image_generation(prompt: str, operation_type: str, dimensions: Optional[str] = "1024x1024", reference_image_url: Optional[str] = None, aspect_ratio: Optional[str] = "1:1", count: Optional[int] = 1, iab_size: Optional[str] = None) -> str:
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
        mock_image_url = f"https://mock-api.com/generated-image-{hash(prompt) % 10000}.jpg"
        return f"Successfully generated image with prompt: '{prompt}'\nDimensions: {dimensions}\nAspect Ratio: {aspect_ratio}\nGenerated Image URL: {mock_image_url}\nImage ID: IMG_{hash(prompt) % 100000}"

    elif operation_type == "multi_generate":
        mock_urls = []
        for i in range(min(count, 4)):
            mock_urls.append(f"https://mock-api.com/generated-image-{hash(prompt) % 10000}-variant-{i+1}.jpg")

        result = f"Successfully generated {len(mock_urls)} image variations with prompt: '{prompt}'\n"
        result += f"Dimensions: {dimensions}\nAspect Ratio: {aspect_ratio}\n"
        result += "Generated Images:\n"
        for i, url in enumerate(mock_urls):
            result += f"  Variant {i+1}: {url} (ID: IMG_{hash(prompt + str(i)) % 100000})\n"
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
            "Large Mobile Banner": "320x100"
        }

        if iab_size in iab_dimensions:
            actual_dimensions = iab_dimensions[iab_size]
            mock_iab_url = f"https://mock-api.com/iab-resized-{iab_size.lower().replace(' ', '-')}-{hash(prompt) % 10000}.jpg"
            return f"Successfully resized image to IAB standard: {iab_size}\nDimensions: {actual_dimensions}\nIAB Resized Image URL: {mock_iab_url}\nImage ID: IMG_{hash(prompt + iab_size) % 100000}_iab"
        else:
            return f"Error: Unsupported IAB size '{iab_size}'. Supported sizes: {', '.join(iab_dimensions.keys())}"

    else:
        return f"Error: Unsupported operation type '{operation_type}'. Supported: generate, resize, multi_generate, resize_to_iab"


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
    "qdrant_search": qdrant_search,
    "redis_cache_operation": redis_cache_operation,
    "postgres_query": postgres_query,
    "image_generation": image_generation,
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
    "qdrant_search": qdrant_search.openai_schema,
    "redis_cache_operation": redis_cache_operation.openai_schema,
    "postgres_query": postgres_query.openai_schema,
    "image_generation": image_generation.openai_schema,
}
