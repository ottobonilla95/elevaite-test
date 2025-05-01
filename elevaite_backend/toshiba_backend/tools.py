import requests
from bs4 import BeautifulSoup
import markdownify
from utils import function_schema
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import dotenv
import os
from utils import client
from rag import get_chunks
import pandas as pd
import requests

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
def get_knowledge(query: str) -> str:
    """Use this RAG tool to ask questions for Toshiba knowledge base. It will return the most relevant chunks of text from the database."""
    res = get_chunks(query)
    return res

@function_schema
def add_numbers(a: int, b: int) -> str:
    """
    Adds two numbers and returns the sum.
    """
    return f"The sum of {a} and {b} is {a + b}"

@function_schema
def get_customer_order(customer_id: int) -> str:
    """"
    Returns the order number for a given customer ID."""
    if customer_id in [i["customer_id"] for i in EXAMPLE_DATA]:
        order_number = [i["order_number"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id][0]
        return f"The order number for customer ID {customer_id} is {order_number}"

@function_schema
def get_customer_location(customer_id: int) -> str:
    """"
    Returns the location for a given customer ID."""
    if customer_id in [i["customer_id"] for i in EXAMPLE_DATA]:
        location = [i["location"] for i in EXAMPLE_DATA if i["customer_id"] == customer_id][0]
        return f"The location for customer ID {customer_id} is {location}"

@function_schema
def add_customer(customer_id: int, order_number: int, location: str) -> str:
    """"
    Adds a new customer to the database."""
    EXAMPLE_DATA.append({"customer_id": customer_id, "order_number": order_number, "location": location})
    return f"Customer ID {customer_id} added successfully."

@function_schema
def weather_forecast(location: str) -> str:
    """"
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
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('body')

        if content:
            markdown_content = markdownify.markdownify(str(content), heading_style="ATX")
            return markdown_content[:20000]
        else:
            return "No content found in the webpage body."

    except requests.RequestException as e:
        return f"Error fetching URL: {e}"

@function_schema
def web_search(query: str,num: Optional[int]=2) -> str:
    """
    You can use this tool to get any information from the web. Just type in your query and get the results.
    """
    num=1
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
        messages=[{"role": "system", "content": f"You're a web search agent."},{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

@function_schema
def get_part_description(part_number: str) -> str:
    """"
    Returns the description for a given part number.
    """

    df = pd.read_csv("toshiba_parts.csv")
    return f"""
    Description: {df[df["Part Number"]==part_number]["Description"].values[0]}
    Assembly Name: {df[df["Part Number"]==part_number]["Assembly Name"].values[0]}
    Image Link: {df[df["Part Number"]==part_number]["Image Link"].values[0]}
    """

@function_schema
def get_part_number(description: str, assembly_name: str) -> str:
    df = pd.read_csv("toshiba_parts.csv")
    """"
    Use this tool to get the part number for a given description and assembly name.
    Or any other information you need from the part list for an assembly.
    """
    part_list = df[(df["Assembly Name"]==assembly_name)].to_string()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"Read the following text and find the part number for the given description."},
                  {"role": "user", "content": part_list+f"\n\nDescription: {description} Give me the part number for the given description."}],
    )
    return response.choices[0].message.content

@function_schema
def query_retriever(query: str) -> str:
    """"
    Use this tool to query the knowledge base. It will return the most relevant chunks of text from the database.
    Questions can include part numbers, assembly names, descriptions and general queries.
    """
    url = "http://localhost:8001/query-chunks"
    params = {
        "query": query,
        "top_k": 3
    }

    # Make the POST request
    response = requests.post(url, params=params)
    res = ""
    sources = []
    for segment in response.json()["selected_segments"]:
        for i,chunk in enumerate(segment["chunks"]):
            # print(chunk['contextual_header'])
            # print(chunk["chunk_text"])
            # print("*"*50)
            res += f"Contextual Header: {chunk['contextual_header']}\n"
            res += f"Chunk {i}:"+chunk["chunk_text"]+"\n"
            res +=f"Filename: {chunk['filename']}, Page Range: {chunk['page_info']}\n"
            res += f"Matched Image Path: {chunk['matched_image_path']}\n"
            res += "\n\n"
    return res

@function_schema
def query_retriever2(query: str) -> list:
    """"
    Use this tool to query the Toshiba knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.
    """
    url = "http://localhost:8001/query-chunks"
    params = {
        "query": query,
        "top_k": 40
    }

    # Make the POST request
    response = requests.post(url, params=params)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    sources = []
    segments = response.json()["selected_segments"][:1]
    for i,segment in enumerate(segments):
        res += "*"*5+f"\n\nSegment {i}"+"\n"
        print(segment["score"])
        for j,chunk in enumerate(segment["chunks"]):
            # res += f"Contextual Header: {chunk['contextual_header']}\n"
            res += f"Article {i}:"+chunk["chunk_text"]+"\n"+"-"*5+"\n"
            res += f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n"
            sources.append(f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n")
            res += "\n\n"
    print(res)
    return [res, sources]


tool_store = {
    "add_numbers": add_numbers,
    "weather_forecast": weather_forecast,
    "url_to_markdown": url_to_markdown,
    "web_search": web_search,
    "get_customer_order": get_customer_order,
    "get_customer_location": get_customer_location,
    "add_customer": add_customer,
    "get_knowledge": get_knowledge,
    "get_part_description": get_part_description,
    "get_part_number": get_part_number,
    "query_retriever": query_retriever,
    "query_retriever2": query_retriever2,
}

tool_schemas = {
    "add_numbers": add_numbers.openai_schema,
    "weather_forecast": weather_forecast.openai_schema,
    "url_to_markdown": url_to_markdown.openai_schema,
    "web_search": web_search.openai_schema,
    "get_customer_order": get_customer_order.openai_schema,
    "get_customer_location": get_customer_location.openai_schema,
    "add_customer": add_customer.openai_schema,
    "get_knowledge": get_knowledge.openai_schema,
    "get_part_description": get_part_description.openai_schema,
    "get_part_number": get_part_number.openai_schema,
    "query_retriever": query_retriever.openai_schema,
    "query_retriever2": query_retriever2.openai_schema,
}

