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


class ToolCall(BaseModel):
    """Represents a tool/function call from the LLM"""

    id: str
    name: str
    arguments: Dict[str, Any]


class TextGenerationResponse(BaseModel):
    latency: float
    text: str
    tokens_in: int
    tokens_out: int
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
