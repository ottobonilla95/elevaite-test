import os
import pytest
from unittest.mock import patch
from elevaite_client.connectors.text_generation.openai import (
    OpenAITextGenerationProvider,
)


@pytest.fixture
def valid_config():
    return {
        "model": "text-davinci-003",
        "temperature": 0.7,
        "max_tokens": 256,
        "retries": 3,
    }


@pytest.fixture
def provider() -> OpenAITextGenerationProvider:
    if openai_api_key := os.getenv("OPENAI_API_KEY"):
        return OpenAITextGenerationProvider(api_key=openai_api_key)
    else:
        raise EnvironmentError


def test_generate_text_success(provider, fake_prompt, valid_config):
    mock_response = {
        "choices": [{"text": "Why don't skeletons fight? They don't have the guts."}]
    }
    with patch("openai.completions.create", return_value=mock_response) as mock_create:
        result = provider.generate_text(fake_prompt, valid_config)

        mock_create.assert_called_once_with(
            model="text-davinci-003",
            prompt=fake_prompt,
            temperature=0.7,
            max_tokens=256,
        )
        assert result == "Why don't skeletons fight? They don't have the guts."


def test_generate_text_retries(provider, fake_prompt, valid_config):
    with patch(
        "openai.completions.create", side_effect=Exception("API error")
    ) as mock_create:
        with pytest.raises(
            RuntimeError, match="Text generation failed after 3 attempts"
        ):
            provider.generate_text(fake_prompt, valid_config)

        assert mock_create.call_count == 3


def test_validate_config_valid(provider, valid_config):
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
