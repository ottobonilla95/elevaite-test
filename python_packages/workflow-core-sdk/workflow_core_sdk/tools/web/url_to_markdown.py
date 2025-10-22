"""
URL to Markdown conversion tool.
"""

import requests
from bs4 import BeautifulSoup
import markdownify
from typing import Optional

try:
    from ..registry import function_schema
except ImportError:
    # Fallback for when imported from Agent Studio
    from utils import function_schema


@function_schema
def url_to_markdown(url: str) -> str:
    """
    Convert a webpage URL to Markdown format.
    
    Fetches the webpage content and converts the HTML body to Markdown.
    Useful for extracting readable text content from web pages.
    
    Args:
        url: The URL of the webpage to convert
        
    Returns:
        str: The webpage content in Markdown format (truncated to 20000 chars)
             or an error message if the fetch fails
    """
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

