import os
import pytest
from unittest.mock import patch
from llm_gateway.models.text_generation.core.base import BaseTextGenerationProvider
from llm_gateway.models.text_generation.openai import (
    OpenAITextGenerationProvider,
)


@pytest.fixture
def provider() -> OpenAITextGenerationProvider:
    if openai_api_key := os.getenv("OPENAI_API_KEY"):
        return OpenAITextGenerationProvider(api_key=openai_api_key)
    else:
        raise EnvironmentError


def test_generate_text_retries(provider: BaseTextGenerationProvider, fake_prompt):
    with patch(
        "openai.completions.create", side_effect=Exception("API error")
    ) as mock_create:
        with pytest.raises(
            RuntimeError, match="Text generation failed after 3 attempts"
        ):
            provider.generate_text(prompt=fake_prompt)

        assert mock_create.call_count == 3


def test_validate_config_valid(provider: BaseTextGenerationProvider, valid_config):
    assert provider.validate_config(valid_config) is True


@pytest.mark.parametrize(
    "invalid_config",
    [
        {},  # Missing model
        {"model": 123},  # Non-string model
        {"model": "text-davinci-003", "temperature": "high"},  # Non-numeric temperature
        {"model": "text-davinci-003", "max_tokens": "a lot"},  # Non-integer max_tokens
    ],
)
def test_validate_config_invalid(provider, invalid_config):
    assert provider.validate_config(invalid_config) is False
