from enum import Enum
from typing import List, Dict, Any, Optional

from openai import BaseModel


class TextGenerationType(str, Enum):
    OPENAI = "openai_textgen"
    ON_PREM = "on-prem_textgen"
    BEDROCK = "bedrock_textgen"
    GEMINI = "gemini_textgen"


class TextGenerationModelName(str, Enum):
    OPENAI_gpt_4o = "gpt-4o"
    OPENAI_gpt_4o_mini = "gpt-4o-mini"
    OPENAI_o1 = "o1"
    GEMINI_1_5_flash = "gemini-1.5-flash"
    BEDROCK_claude_instant_v1 = "anthropic.claude-instant-v1"
    BEDROCK_llama3_3_70b_instruct_v1 = "meta.llama3-3-70b-instruct-v1:0"


class ToolCallFunction(BaseModel):
    """OpenAI-style function object within a ToolCall."""

    name: str
    arguments: str  # JSON string of arguments

    model_config = {"frozen": True}


class ToolCall(BaseModel):
    """Represents a tool/function call from the LLM.

    Provides both direct access (tc.name, tc.arguments) and OpenAI-style
    access (tc.function.name, tc.function.arguments) for compatibility.
    """

    id: str
    name: str
    arguments: Dict[str, Any]

    @property
    def function(self) -> ToolCallFunction:
        """OpenAI-compatible function accessor."""
        import json

        args_str = json.dumps(self.arguments) if isinstance(self.arguments, dict) else str(self.arguments)
        return ToolCallFunction(name=self.name, arguments=args_str)


class TextGenerationResponse(BaseModel):
    latency: float
    text: str
    tokens_in: int
    tokens_out: int
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    thinking_content: Optional[str] = None  # Reasoning/thinking data from models that support it
