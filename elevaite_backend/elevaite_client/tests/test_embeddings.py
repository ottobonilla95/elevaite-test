import os
import pytest
from elevaite_client.connectors.embeddings.openai import OpenAIEmbeddingProvider
from elevaite_client.connectors.embeddings.core.interfaces import (
    EmbeddingInfo,
    EmbeddingType,
)


def test_openai_embedding():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    provider = OpenAIEmbeddingProvider(api_key=api_key)

    embedding_info = EmbeddingInfo(
        type=EmbeddingType.OPENAI,
        name="text-embedding-ada-002",
        dimensions=1536,
        inference_url=None,  # OpenAI doesn't use inference URL
    )

    texts = ["Hello, world!", "This is a test embedding"]

    try:
        embeddings = provider.embed_documents(texts, embedding_info)

        # Basic validations
        assert len(embeddings) == len(texts)
        assert len(embeddings[0]) == 1536
        assert all(len(emb) == 1536 for emb in embeddings)
    except Exception as e:
        pytest.fail(f"Embedding test failed: {e}")


def test_openai_provider_validation():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    provider = OpenAIEmbeddingProvider(api_key=api_key)

    valid_info = EmbeddingInfo(
        type=EmbeddingType.OPENAI,
        name="text-embedding-ada-002",
        dimensions=1536,
        inference_url="",
    )
    assert provider.validate_config(valid_info) is True

    invalid_type_info = EmbeddingInfo(
        type=EmbeddingType.LOCAL,
        name="text-embedding-ada-002",
        dimensions=1536,
        inference_url="",
    )
    assert provider.validate_config(invalid_type_info) is False
