import pytest
import logging

from elevaite_client.connectors.text_generation.core.interfaces import (
    TextGenerationType,
)
from elevaite_client.rpc.client import TextGenerationService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_generate_text_with_openai(model_provider_factory):
    """
    Test the text generation service using OpenAI API.
    Logs the response after the test.
    """
    service = TextGenerationService(model_provider_factory)

    prompt = "Write a short story about a space adventure."
    config = {
        "type": TextGenerationType.OPENAI,
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 50,
    }

    try:
        response = service.generate_text(prompt, config)

        logger.info(f"OpenAI Response: {response}")

        assert isinstance(response, str)
        assert len(response) > 0

    except Exception as e:
        pytest.fail(f"OpenAI text generation test failed: {str(e)}")
