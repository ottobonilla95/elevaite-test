"""
Tools module for LLM Gateway.

Provides fallback implementations for built-in tools that aren't supported
by all providers (e.g., web search for Bedrock and On-Prem).
"""

from .web_search import web_search, WebSearchResult

__all__ = ["web_search", "WebSearchResult"]

