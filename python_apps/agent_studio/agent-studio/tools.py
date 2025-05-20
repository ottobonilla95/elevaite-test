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


tool_store = {
    "add_numbers": add_numbers,
    "weather_forecast": weather_forecast,
    "url_to_markdown": url_to_markdown,
    "web_search": web_search,
    "get_customer_order": get_customer_order,
    "get_customer_location": get_customer_location,
    "add_customer": add_customer,
}

tool_schemas = {
    "add_numbers": add_numbers.openai_schema,
    "weather_forecast": weather_forecast.openai_schema,
    "url_to_markdown": url_to_markdown.openai_schema,
    "web_search": web_search.openai_schema,
    "get_customer_order": get_customer_order.openai_schema,
    "get_customer_location": get_customer_location.openai_schema,
    "add_customer": add_customer.openai_schema,
}
