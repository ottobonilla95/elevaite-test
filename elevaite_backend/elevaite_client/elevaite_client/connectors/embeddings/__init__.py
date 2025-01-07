from typing import List
import uuid
import tiktoken

from ...connectors.embeddings import bedrock, onprem, gemini
from .core.interfaces import EmbeddingType, EmbeddingInfo, EmbeddingResult, ChunkAsJson
from . import openai, elevaite


def get_token_size(content: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(content))
    return num_tokens


def __get_embedder(type: EmbeddingType):
    match type:
        case EmbeddingType.OPENAI:
            return openai.BaseEmbeddingProvider.embed_documents
        case EmbeddingType.BEDROCK:
            return bedrock.BaseEmbeddingProvider.embed_documents
        case EmbeddingType.ON_PREM:
            return onprem.BaseEmbeddingProvider.embed_documents
        case EmbeddingType.LOCAL:
            return elevaite.BaseEmbeddingProvider.embed_documents
        case EmbeddingType.EXTERNAL:
            raise NotImplementedError("External embeddings not implemented yet")
        case _:
            raise Exception("Invalid Embedding Type")


def embed_documents(
    payloads_with_content: List[ChunkAsJson], info: EmbeddingInfo
) -> List[EmbeddingResult]:
    embedder = __get_embedder(type=info.type)
    res: List[EmbeddingResult] = []

    for payload in payloads_with_content:
        if payload.page_content:
            token_size = get_token_size(payload.page_content)
            payload.metadata["tokenSize"] = token_size
            vectors = embedder(texts=[payload.page_content], info=info)
            id = str(uuid.uuid4())
            res.append(
                EmbeddingResult(
                    payload=payload, vectors=vectors, token_size=token_size, id=id
                )
            )

    return res
