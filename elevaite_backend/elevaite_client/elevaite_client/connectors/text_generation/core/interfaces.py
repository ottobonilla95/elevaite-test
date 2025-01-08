from enum import Enum


class TextGenerationType(str, Enum):
    OPENAI = "openai_textgen"
    ON_PREM = "on-prem_textgen"
    BEDROCK = "bedrock_textgen"
    GEMINI = "gemini_textgen"
    LOCAL = "local_textgen"
    EXTERNAL = "external_textgen"
