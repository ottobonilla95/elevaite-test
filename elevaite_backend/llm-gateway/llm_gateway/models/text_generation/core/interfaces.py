from enum import Enum

from openai import BaseModel


class TextGenerationType(str, Enum):
    OPENAI = "openai_textgen"
    ON_PREM = "on-prem_textgen"
    BEDROCK = "bedrock_textgen"
    GEMINI = "gemini_textgen"


class TextGenerationResponse(BaseModel):
    latency: float
    text: str
    tokens_in: int
    tokens_out: int
