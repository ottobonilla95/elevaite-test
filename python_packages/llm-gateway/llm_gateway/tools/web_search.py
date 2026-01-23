"""
Web search tool for LLM Gateway.

Provides a fallback web search implementation using Google Custom Search API
for providers that don't have built-in web search support (Bedrock, On-Prem).
"""

import os
import logging
import requests
from typing import Optional, List
from dataclasses import dataclass
from bs4 import BeautifulSoup
import markdownify


# Environment variables for Google Custom Search API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_PERSONAL")
GOOGLE_SEARCH_CX_ID = os.getenv("GOOGLE_SEARCH_CX_ID") or os.getenv("CX_ID_PERSONAL")


@dataclass
class WebSearchResult:
    """Represents a single web search result."""
    title: str
    url: str
    snippet: str
    content: Optional[str] = None


def url_to_markdown(url: str, max_chars: int = 20000) -> str:
    """
    Convert a webpage URL to Markdown format.
    
    Args:
        url: The URL of the webpage to convert
        max_chars: Maximum characters to return (default: 20000)
        
    Returns:
        The webpage content in Markdown format or an error message
    """
    try:
        response = requests.get(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (compatible; LLMGateway/1.0)"},
            timeout=10
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        content = soup.find("body")

        if content:
            markdown_content = markdownify.markdownify(
                str(content), heading_style="ATX"
            )
            return markdown_content[:max_chars]
        else:
            return "No content found in the webpage body."

    except requests.RequestException as e:
        logging.warning(f"Error fetching URL {url}: {e}")
        return f"Error fetching URL: {e}"


def web_search(
    query: str, 
    num_results: int = 3,
    fetch_content: bool = True,
    max_content_chars: int = 10000,
) -> List[WebSearchResult]:
    """
    Perform a web search using Google Custom Search API.
    
    This is a fallback implementation for providers that don't have
    built-in web search support (Bedrock, On-Prem).
    
    Args:
        query: The search query
        num_results: Number of results to return (default: 3, max: 10)
        fetch_content: Whether to fetch and convert page content to markdown
        max_content_chars: Maximum characters per page content
        
    Returns:
        List of WebSearchResult objects
        
    Raises:
        ValueError: If Google API credentials are not configured
        RuntimeError: If the search request fails
    """
    if not GOOGLE_API_KEY or not GOOGLE_SEARCH_CX_ID:
        raise ValueError(
            "Google Custom Search API credentials not configured. "
            "Set GOOGLE_API_KEY and GOOGLE_SEARCH_CX_ID environment variables."
        )
    
    num_results = min(max(1, num_results), 10)  # Clamp between 1 and 10
    
    try:
        # Perform Google Custom Search
        search_url = (
            f"https://www.googleapis.com/customsearch/v1"
            f"?q={requests.utils.quote(query)}"
            f"&key={GOOGLE_API_KEY}"
            f"&cx={GOOGLE_SEARCH_CX_ID}"
            f"&num={num_results}"
        )
        
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        
        search_data = response.json()
        
        if "items" not in search_data:
            logging.info(f"No search results found for query: {query}")
            return []
        
        results = []
        for item in search_data["items"]:
            result = WebSearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
            )
            
            # Optionally fetch full page content
            if fetch_content and result.url:
                result.content = url_to_markdown(result.url, max_content_chars)
            
            results.append(result)
        
        return results
        
    except requests.RequestException as e:
        logging.error(f"Web search request failed: {e}")
        raise RuntimeError(f"Web search failed: {e}")


def format_search_results(results: List[WebSearchResult], include_content: bool = True) -> str:
    """
    Format search results as a readable string for LLM consumption.
    
    Args:
        results: List of WebSearchResult objects
        include_content: Whether to include full page content
        
    Returns:
        Formatted string with search results
    """
    if not results:
        return "No search results found."
    
    formatted = []
    for i, result in enumerate(results, 1):
        parts = [
            f"## Result {i}: {result.title}",
            f"**URL:** {result.url}",
            f"**Snippet:** {result.snippet}",
        ]
        if include_content and result.content:
            parts.append(f"\n**Content:**\n{result.content}")
        formatted.append("\n".join(parts))
    
    return "\n\n---\n\n".join(formatted)

