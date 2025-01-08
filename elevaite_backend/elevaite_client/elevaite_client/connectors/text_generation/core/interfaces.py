from enum import Enum


class TextGenerationType(str, Enum):
    OPENAI = "openai"
    ON_PREM = "on-prem"
    BEDROCK = "bedrock"
    GEMINI = "gemini"
    LOCAL = "local"
    EXTERNAL = "external"
