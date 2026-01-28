from pydantic import BaseModel
from typing import Optional, Dict, Any
from utils import log_decorator

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


# Define query transformer