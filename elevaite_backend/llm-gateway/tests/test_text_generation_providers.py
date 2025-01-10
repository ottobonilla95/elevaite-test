import pytest
import logging

from llm_gateway.models.text_generation.core.interfaces import (
    TextGenerationType,
)
from llm_gateway.services import TextGenerationService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_textgen_test(
    prompt: str, model: str, provider_type: TextGenerationType, model_provider_factory
):
    service = TextGenerationService(model_provider_factory)

    config = {
        "type": provider_type,
        "model": model,
        "temperature": 0.7,
        "max_tokens": 50,
        "retries": 3,
    }

    try:
        response = service.generate_text(prompt, config)

        logger.info(f"{provider_type} Response: {response}")

        assert isinstance(response, str)
        assert len(response) > 0

    except Exception as e:
        pytest.fail(f"{provider_type} text generation test failed: {str(e)}")


def test_generate_text_with_onprem(model_provider_factory, fake_prompt):
    """
    Test the text generation service using the On-Prem API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="Llama-3.1-8B-Instruct",
        provider_type=TextGenerationType.ON_PREM,
        prompt=fake_prompt,
        model_provider_factory=model_provider_factory,
    )


def test_generate_text_with_openai(model_provider_factory, fake_prompt):
    """
    Test the text generation service using OpenAI API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="gpt-4o",
        provider_type=TextGenerationType.OPENAI,
        prompt=fake_prompt,
        model_provider_factory=model_provider_factory,
    )


def test_generate_text_with_gemini(model_provider_factory, fake_prompt):
    """
    Test the text generation service using Gemini API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="gemini-1.5-flash",
        provider_type=TextGenerationType.GEMINI,
        prompt=fake_prompt,
        model_provider_factory=model_provider_factory,
    )


def test_generate_text_with_bedrock_for_anthropic(model_provider_factory, fake_prompt):
    """
    Test the text generation service using an Anthropic API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="anthropic.claude-instant-v1",
        provider_type=TextGenerationType.BEDROCK,
        prompt=fake_prompt,
        model_provider_factory=model_provider_factory,
    )


def test_generate_text_with_bedrock_for_llama(model_provider_factory, fake_prompt):
    """
    Test the text generation service using a Llama API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="meta.llama3-3-70b-instruct-v1:0",
        provider_type=TextGenerationType.BEDROCK,
        prompt=fake_prompt,
        model_provider_factory=model_provider_factory,
    )
