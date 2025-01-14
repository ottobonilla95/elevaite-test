from enum import Enum
from typing import TypedDict


class TextGenerationType(str, Enum):
    OPENAI = "openai_textgen"
    ON_PREM = "on-prem_textgen"
    BEDROCK = "bedrock_textgen"
    GEMINI = "gemini_textgen"


class TextGenerationResponse(TypedDict):
    latency: float
    text: str
    tokens_in: int
    tokens_out: int
