from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from utils import log_decorator
from tools import web_search

class Component(BaseModel):
    name: str
    description: Optional[str]
    input_type: Optional[str] = "text"
    output_type: Optional[str] = "text"
    parameters: Dict[str, Any]
    # logs: Dict[str, List] = Field(default_factory=lambda: {"input": [], "output": []})

    @log_decorator
    def execute(self, **kwargs) -> Any:
        """Execution script for each component."""
        raise NotImplementedError("Component execution logic should be implemented in subclasses.")

class WebSearchComponent(Component):
    search_engine: Optional[str] = "google"

    @log_decorator
    def execute(self, query: str) -> Any:
        """Performs a web search using Google or Bing API."""
        return web_search(query)