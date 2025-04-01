import pytest
import os
from unittest.mock import patch

from llm_gateway.models.embeddings.core.interfaces import EmbeddingType
from llm_gateway.models.provider import ModelProviderFactory
from llm_gateway.models.text_generation.core.interfaces import (
    TextGenerationType,
)


@patch.dict(os.environ, {"OPENAI_API_KEY": "test_openai_key"})
def test_openai_provider_initialization():
    factory = ModelProviderFactory()
    assert EmbeddingType.OPENAI in factory.providers
    assert TextGenerationType.OPENAI in factory.providers


@patch.dict(os.environ, {"BEDROCK_REGION": "us-west-2"})
def test_bedrock_provider_initialization():
    factory = ModelProviderFactory()
    assert EmbeddingType.BEDROCK in factory.providers


def test_get_provider():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_gemini_key"}):
        factory = ModelProviderFactory()
        provider = factory.get_provider(TextGenerationType.OPENAI)
        assert provider is not None

    with pytest.raises(ValueError):
        factory.get_provider("INVALID_TYPE")
