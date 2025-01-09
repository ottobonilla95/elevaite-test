import logging
import pytest

from llm_gateway.models.embeddings.core.interfaces import (
    EmbeddingInfo,
    EmbeddingRequest,
    EmbeddingType,
)
from llm_gateway.services import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_embed_documents_with_onprem(model_provider_factory):
    """
    Test the embedding service using OnPrem API.
    Logs the embeddings and the full response after the test.
    """
    service = EmbeddingService(model_provider_factory)

    request = EmbeddingRequest(
        texts=["This is a test document.", "Another test input."],
        info=EmbeddingInfo(
            type=EmbeddingType.ON_PREM,
            name="custom-embedding-model",
            inference_url=None,
        ),
        metadata={"source": "unit_test"},
    )

    try:
        response = service.embed(request)

        logger.info(f"Full Response: {response}")
        logger.info(f"OnPrem Embeddings: {response.vectors}")

        assert isinstance(response.vectors, list), "Response vectors should be a list"
        assert len(response.vectors) == len(
            request.texts
        ), f"Expected {len(request.texts)} vectors, but got {len(response.vectors)}"
        assert all(
            isinstance(vector, list) for vector in response.vectors
        ), "Each vector should be a list"
        assert all(
            len(vector) > 0 for vector in response.vectors
        ), "Each vector should have dimensions"

    except Exception as e:
        logger.error(f"OnPrem embedding test failed: {str(e)}")
        pytest.fail(f"OnPrem embedding test failed: {str(e)}")


def test_embed_documents_with_openai(model_provider_factory):
    """
    Test the embedding service using OpenAI API.
    Logs the embeddings after the test.
    """
    service = EmbeddingService(model_provider_factory)

    request = EmbeddingRequest(
        texts=["This is a test document.", "Another test input."],
        info=EmbeddingInfo(
            type=EmbeddingType.OPENAI,
            name="text-embedding-ada-002",
            inference_url=None,  # OpenAI doesn't use inference_url
        ),
        metadata={"source": "unit_test"},
    )

    try:
        response = service.embed(request)

        logger.info(f"OpenAI Embeddings: {response.vectors}")

        assert isinstance(response.vectors, list), "Response vectors should be a list"
        assert len(response.vectors) == len(request.texts), "One vector per input text"
        assert all(
            isinstance(vector, list) for vector in response.vectors
        ), "Each vector should be a list"
        assert all(
            len(vector) > 0 for vector in response.vectors
        ), "Each vector should have dimensions"

    except Exception as e:
        pytest.fail(f"OpenAI embedding test failed: {str(e)}")


def test_embed_documents_with_gemini(model_provider_factory):
    """
    Test the embedding service using Gemini API.
    Logs the embeddings after the test.
    """
    service = EmbeddingService(model_provider_factory)

    request = EmbeddingRequest(
        texts=["This is a test document.", "Another test input."],
        info=EmbeddingInfo(
            type=EmbeddingType.GEMINI,
            name="models/text-embedding-004",
            inference_url=None,  # Gemini doesn't use inference_url
        ),
        metadata={"source": "unit_test"},
    )

    try:
        response = service.embed(request)

        logger.info(f"Gemini Embeddings: {response.vectors}")

        assert isinstance(response.vectors, list), "Response vectors should be a list"
        assert len(response.vectors) == len(request.texts), "One vector per input text"
        assert all(
            isinstance(vector, list) for vector in response.vectors
        ), "Each vector should be a list"
        assert all(
            len(vector) > 0 for vector in response.vectors
        ), "Each vector should have dimensions"

    except Exception as e:
        pytest.fail(f"Gemini embedding test failed: {str(e)}")
