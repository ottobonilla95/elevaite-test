import logging
import pytest

from llm_gateway.models.embeddings.core.interfaces import (
    EmbeddingInfo,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingType,
)
from llm_gateway.services import UniversalService, RequestType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_embedding_response(
    response: EmbeddingResponse, request: EmbeddingRequest, api_name: str
):
    """
    Common validation logic for embedding responses.
    Logs embeddings and performs assertions.
    """
    try:
        logger.info(f"{api_name} Embeddings: {response.embeddings}")

        assert response.embeddings
        assert response.latency
        assert response.tokens_in >= 0
    except Exception as e:
        logger.error(f"{api_name} embedding test failed: {str(e)}")
        pytest.fail(f"{api_name} embedding test failed: {str(e)}")


def create_embedding_request(provider_type, model_name):
    """
    Helper function to create an embedding request.
    """
    return EmbeddingRequest(
        texts=["This is a test document.", "Another test input."],
        info=EmbeddingInfo(
            type=provider_type,
            name=model_name,
        ),
        metadata={"source": "unit_test"},
    )


def test_embed_documents_with_onprem():
    """
    Test the embedding service using OnPrem API.
    """
    service = UniversalService()

    request = create_embedding_request(
        EmbeddingType.ON_PREM, "Snowflake--snowflake-arctic-embed-m"
    )

    response = service.handle_request(
        request_type=RequestType.EMBEDDING,
        provider_type=EmbeddingType.ON_PREM,
        texts=request.texts,
        info=request.info,
    )
    validate_embedding_response(
        response, request, "Snowflake--snowflake-arctic-embed-m"
    )


def test_embed_documents_with_openai():
    """
    Test the embedding service using OpenAI API.
    """
    service = UniversalService()

    request = create_embedding_request(EmbeddingType.OPENAI, "text-embedding-ada-002")

    response = service.handle_request(
        request_type=RequestType.EMBEDDING,
        provider_type=EmbeddingType.OPENAI,
        texts=request.texts,
        info=request.info,
    )
    validate_embedding_response(response, request, "OpenAI")


def test_embed_documents_with_gemini():
    """
    Test the embedding service using Gemini API.
    """
    service = UniversalService()

    request = create_embedding_request(
        EmbeddingType.GEMINI, "models/text-embedding-004"
    )

    response = service.handle_request(
        request_type=RequestType.EMBEDDING,
        provider_type=EmbeddingType.GEMINI,
        texts=request.texts,
        info=request.info,
    )
    validate_embedding_response(response, request, "Gemini")


def test_embed_documents_with_bedrock_with_anthropic():
    """
    Test the embedding service using AWS Bedrock.
    """
    service = UniversalService()

    request = create_embedding_request(
        EmbeddingType.BEDROCK, "anthropic.claude-instant-v1"
    )

    response = service.handle_request(
        request_type=RequestType.EMBEDDING,
        provider_type=EmbeddingType.BEDROCK,
        texts=request.texts,
        info=request.info,
    )
    validate_embedding_response(response, request, "Bedrock")
