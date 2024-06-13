from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EmbeddingType(str, Enum):
    OPENAI = "openai"
    LOCAL = "local"
    EXTERNAL = "external"


class EmbeddingInfo(BaseModel):
    type: EmbeddingType
    inference_url: Optional[str]
    name: str
    dimensions: int


class EmbeddingResult(BaseModel):
    payload: "ChunkAsJson"
    vectors: List[List[float]]
    id: str
    token_size: int


class ChunkAsJson(BaseModel):
    metadata: Dict[str, Any]
    page_content: str
