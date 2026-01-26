"""
Web search tool using Google Custom Search API.
"""

import os
import requests
from typing import Optional
from openai import OpenAI

try:
    from ..registry import function_schema
    from .url_to_markdown import url_to_markdown
except ImportError:
    # Fallback for when imported from Agent Studio
    from utils import function_schema
    from .url_to_markdown import url_to_markdown


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google API credentials
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")
CX_ID = os.getenv("CX_ID_PERSONAL")


@function_schema
def web_search(query: str, num: Optional[int] = 2) -> str:
    """
    Search the web using Google Custom Search and return AI-summarized results.

    Performs a Google search, fetches the top result, converts it to markdown,
    and uses GPT-4 to generate a concise answer to the query.

    Args:
        query: The search query
        num: Number of results to fetch (default: 2, currently limited to 1)

    Returns:
        str: AI-generated answer based on web search results
    """
    # Currently limited to 1 result for performance
    num = 1

    try:
        # Perform Google Custom Search
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API}&cx={CX_ID}&num={num}"
        response = requests.get(url)
        response.raise_for_status()

        # Extract URLs from search results
        search_data = response.json()
        if "items" not in search_data:
            return "No search results found."

        urls = [item["link"] for item in search_data["items"]]

        # Convert URLs to markdown
        text = "\n".join([url_to_markdown(url) for url in urls])

        # Use GPT-4 to summarize and answer the query
        prompt = f"Use the following text to answer the given: {query} \n\n ---BEGIN WEB TEXT --- {text} ---END WEB TEXT --- "

        ai_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You're a web search agent."},
                {"role": "user", "content": prompt},
            ],
        )

        if ai_response.choices[0].message.content is not None:
            return ai_response.choices[0].message.content
        return ""

    except requests.RequestException as e:
        return f"Error performing web search: {e}"
    except Exception as e:
        return f"Error processing search results: {e}"
