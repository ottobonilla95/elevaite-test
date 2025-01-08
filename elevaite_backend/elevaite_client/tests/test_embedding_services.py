import logging
import pytest

from elevaite_client.connectors.embeddings.core.interfaces import (
    EmbeddingInfo,
    EmbeddingRequest,
    EmbeddingType,
)
from elevaite_client.rpc.client import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            inference_url="",  # OpenAI doesn't use inference_url
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
