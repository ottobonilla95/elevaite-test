from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EmbeddingType(str, Enum):
    OPENAI = "openai_embedding"
    ON_PREM = "on-prem_embedding"
    BEDROCK = "bedrock_embedding"
    GEMINI = "gemini_embedding"


class EmbeddingInfo(BaseModel):
    type: EmbeddingType
    name: str
    dimensions: int = 1536  # Default OpenAI dimension


class EmbeddingResult(BaseModel):
    payload: "ChunkAsJson"
    vectors: List[List[float]]
    id: str
    token_size: int


class EmbeddingRequest(BaseModel):
    texts: List[str]
    info: EmbeddingInfo
    metadata: Dict[str, Any] = {}


class EmbeddingResponse(BaseModel):
    vectors: List[List[float]]
    metadata: Dict[str, Any] = {}


class ChunkAsJson(BaseModel):
    metadata: Dict[str, Any]
    page_content: str
