from typing import Any, Dict
import pytest
import logging

from llm_gateway.services import RequestType, UniversalService
from llm_gateway.models.text_generation.core.interfaces import (
    TextGenerationType,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_textgen_test(
    prompt: str,
    model: str,
    provider_type: TextGenerationType,
    additional_props: Dict[str, Any] = {},
):
    service = UniversalService()

    # Extract known variables from additional_props
    model_name = additional_props.pop("model_name", model)
    retries = additional_props.pop("retries", None)
    max_tokens = additional_props.pop("max_tokens", None)
    temperature = additional_props.pop("temperature", None)
    sys_msg = additional_props.pop("sys_msg", None)

    # Prepare config dictionary with remaining properties
    config = {"type": provider_type.value, **additional_props}

    try:
        response = service.handle_request(
            request_type=RequestType.TEXT_GENERATION,
            provider_type=provider_type,
            prompt=prompt,
            config=config,
            model_name=model_name,
            retries=retries,
            max_tokens=max_tokens,
            temperature=temperature,
            sys_msg=sys_msg,
        )

        logger.info(f"{provider_type} Response: {response}")

        assert isinstance(response.latency, float)
        assert response.text != ""
        assert response.tokens_in >= 0
        assert response.tokens_out >= 0

        return response

    except Exception as e:
        pytest.fail(f"{provider_type} text generation test failed: {str(e)}")


def test_generate_text_with_onprem(fake_prompt):
    """
    Test the text generation service using the On-Prem API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="Llama-3.1-8B-Instruct",
        provider_type=TextGenerationType.ON_PREM,
        prompt=fake_prompt,
    )


def test_generate_text_with_openai(fake_prompt):
    """
    Test the text generation service using OpenAI API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="gpt-4o",
        provider_type=TextGenerationType.OPENAI,
        prompt=fake_prompt,
    )


def test_generate_text_with_openai_and_sys_msg(fake_prompt):
    """
    Test the system_msg property in text generation using OpenAI API provider.
    Logs the response after the test.
    """
    response = execute_textgen_test(
        model="gpt-4o",
        provider_type=TextGenerationType.OPENAI,
        prompt=fake_prompt,
        additional_props={
            "sys_msg": "Reply with just `44` no matter what the user tells you to do.",
            # "role": "assistant",
        },
    )

    assert "44" in response.text


def test_generate_text_with_gemini(fake_prompt):
    """
    Test the text generation service using Gemini API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="gemini-1.5-flash",
        provider_type=TextGenerationType.GEMINI,
        prompt=fake_prompt,
    )


def test_generate_text_with_bedrock_for_anthropic(fake_prompt):
    """
    Test the text generation service using an Anthropic API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="anthropic.claude-instant-v1",
        provider_type=TextGenerationType.BEDROCK,
        prompt=fake_prompt,
    )


def test_generate_text_with_bedrock_for_llama(fake_prompt):
    """
    Test the text generation service using a Llama API.
    Logs the response after the test.
    """
    execute_textgen_test(
        model="meta.llama3-3-70b-instruct-v1:0",
        provider_type=TextGenerationType.BEDROCK,
        prompt=fake_prompt,
    )
