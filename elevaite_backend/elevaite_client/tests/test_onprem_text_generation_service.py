import pytest
import logging

from elevaite_client.connectors.text_generation.core.interfaces import (
    TextGenerationType,
)
from elevaite_client.rpc.client import TextGenerationService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_generate_text_with_onprem(model_provider_factory, fake_prompt):
    """
    Test the text generation service using the On-Prem API.
    Logs the response after the test.
    """
    service = TextGenerationService(model_provider_factory)

    config = {
        "type": TextGenerationType.ON_PREM,
        "model": "Llama-3.1-8B-Instruct",
        "temperature": 0.7,
        "max_tokens": 50,
        "retries": 3,
    }

    try:
        response = service.generate_text(fake_prompt, config)

        logger.info(f"On-Prem Response: {response}")

        assert isinstance(response, str)
        assert len(response) > 0

    except Exception as e:
        pytest.fail(f"On-Prem text generation test failed: {str(e)}")
