from enum import Enum


class VisionType(str, Enum):
    OPENAI = "openai_vision"
    ON_PREM = "on-prem_vision"
    BEDROCK = "bedrock_vision"
    GEMINI = "gemini_vision"
