"""Unit tests for OpenAI providers using mocking."""

import pytest
from unittest.mock import Mock

from llm_gateway.models.text_generation.openai import OpenAITextGenerationProvider
from llm_gateway.models.embeddings.openai import OpenAIEmbeddingProvider
from llm_gateway.models.vision.openai import OpenAIVisionProvider
from llm_gateway.models.embeddings.core.interfaces import EmbeddingInfo, EmbeddingType


class TestOpenAITextGenerationProvider:
    """Unit tests for OpenAITextGenerationProvider"""

    def test_generate_text_success(self):
        """Test successful text generation"""
        # Create mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This is a test response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        provider = OpenAITextGenerationProvider(api_key="test-key")
        # Mock the client's chat.completions.create method
        provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = provider.generate_text(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="Hello",
            retries=1,
            config={},
        )

        assert result.text == "This is a test response"
        assert result.tokens_in == 10
        assert result.tokens_out == 5
        assert result.latency > 0
        assert result.finish_reason == "stop"
        assert result.tool_calls is None

    def test_generate_text_with_tools(self):
        """Test text generation with tool calls"""
        # Create mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "NYC"}'

        # Create mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 10

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = provider.generate_text(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="What's the weather in NYC?",
            retries=1,
            config={},
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get weather",
                        "parameters": {
                            "type": "object",
                            "properties": {"location": {"type": "string"}},
                        },
                    },
                }
            ],
        )

        assert result.text == ""
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == {"location": "NYC"}
        assert result.finish_reason == "tool_calls"

    def test_generate_text_with_messages(self):
        """Test text generation with message history"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "I remember our previous conversation"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 30
        mock_response.usage.completion_tokens = 8

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = provider.generate_text(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="Do you remember?",
            retries=1,
            config={},
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "Do you remember?"},
            ],
        )

        assert result.text == "I remember our previous conversation"
        assert result.tokens_in == 30
        assert result.tokens_out == 8

    def test_generate_text_api_error(self):
        """Test handling of API errors"""
        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.chat.completions.create = Mock(side_effect=Exception("API Error"))

        with pytest.raises(RuntimeError, match="Text generation failed after 1 attempts"):
            provider.generate_text(
                model_name="gpt-4o",
                temperature=0.7,
                max_tokens=100,
                sys_msg="You are a helpful assistant",
                prompt="Hello",
                retries=1,
                config={},
            )

    def test_stream_text_success(self):
        """Test successful streaming text generation"""
        # Create mock stream chunks
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock()]
        mock_chunk1.choices[0].delta = Mock()
        mock_chunk1.choices[0].delta.content = "Hello"
        mock_chunk1.choices[0].delta.role = "assistant"
        mock_chunk1.choices[0].delta.tool_calls = None  # Important: must be None, not a Mock
        mock_chunk1.choices[0].finish_reason = None

        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta = Mock()
        mock_chunk2.choices[0].delta.content = " world"
        mock_chunk2.choices[0].delta.tool_calls = None
        mock_chunk2.choices[0].finish_reason = None

        mock_chunk3 = Mock()
        mock_chunk3.choices = [Mock()]
        mock_chunk3.choices[0].delta = Mock()
        mock_chunk3.choices[0].delta.content = None
        mock_chunk3.choices[0].delta.tool_calls = None
        mock_chunk3.choices[0].finish_reason = "stop"

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.chat.completions.create = Mock(return_value=iter([mock_chunk1, mock_chunk2, mock_chunk3]))

        stream = provider.stream_text(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="Hello",
            retries=1,
            config={},
        )

        chunks = list(stream)
        assert len(chunks) > 0
        # Verify we got some delta chunks
        delta_chunks = [c for c in chunks if c.get("type") == "delta"]
        assert len(delta_chunks) > 0


class TestOpenAIEmbeddingProvider:
    """Unit tests for OpenAIEmbeddingProvider"""

    def test_embed_documents_success(self):
        """Test successful document embedding"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 5

        provider = OpenAIEmbeddingProvider(api_key="test-key")
        provider.client.embeddings.create = Mock(return_value=mock_response)

        info = EmbeddingInfo(type=EmbeddingType.OPENAI, name="text-embedding-ada-002")
        result = provider.embed_documents(texts=["Hello world"], info=info)

        assert len(result.embeddings) == 1
        assert result.embeddings[0] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert result.tokens_in == 5
        assert result.latency > 0

    def test_embed_documents_multiple(self):
        """Test embedding multiple documents"""
        mock_response1 = Mock()
        mock_response1.data = [Mock()]
        mock_response1.data[0].embedding = [0.1, 0.2, 0.3]
        mock_response1.usage = Mock()
        mock_response1.usage.total_tokens = 3

        mock_response2 = Mock()
        mock_response2.data = [Mock()]
        mock_response2.data[0].embedding = [0.4, 0.5, 0.6]
        mock_response2.usage = Mock()
        mock_response2.usage.total_tokens = 4

        provider = OpenAIEmbeddingProvider(api_key="test-key")
        provider.client.embeddings.create = Mock(side_effect=[mock_response1, mock_response2])

        info = EmbeddingInfo(type=EmbeddingType.OPENAI, name="text-embedding-ada-002")
        result = provider.embed_documents(texts=["First doc", "Second doc"], info=info)

        assert len(result.embeddings) == 2
        assert result.embeddings[0] == [0.1, 0.2, 0.3]
        assert result.embeddings[1] == [0.4, 0.5, 0.6]
        assert result.tokens_in == 7  # 3 + 4

    def test_embed_documents_api_error(self):
        """Test handling of API errors"""
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        provider.client.embeddings.create = Mock(side_effect=Exception("API Error"))

        info = EmbeddingInfo(type=EmbeddingType.OPENAI, name="text-embedding-ada-002")

        with pytest.raises(RuntimeError, match="Embedding failed after 3 attempts"):
            provider.embed_documents(texts=["Hello world"], info=info)


class TestOpenAIVisionProvider:
    """Unit tests for OpenAIVisionProvider"""

    def test_generate_text_success(self):
        """Test successful image processing"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This image shows a cat"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10

        provider = OpenAIVisionProvider(api_key="test-key")
        provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = provider.generate_text(
            images=["https://example.com/cat.jpg"],
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="What's in this image?",
            retries=1,
            config={},
        )

        assert result.text == "This image shows a cat"
        assert result.tokens_in == 100
        assert result.tokens_out == 10
        assert result.latency > 0

    def test_generate_text_multiple_images(self):
        """Test processing multiple images"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "The first image shows a cat, the second shows a dog"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 15

        provider = OpenAIVisionProvider(api_key="test-key")
        provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = provider.generate_text(
            images=["https://example.com/cat.jpg", "https://example.com/dog.jpg"],
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="What's in these images?",
            retries=1,
            config={},
        )

        assert result.text == "The first image shows a cat, the second shows a dog"
        assert result.tokens_in == 200
        assert result.tokens_out == 15

    def test_generate_text_api_error(self):
        """Test handling of API errors"""
        provider = OpenAIVisionProvider(api_key="test-key")
        provider.client.chat.completions.create = Mock(side_effect=Exception("API Error"))

        with pytest.raises(RuntimeError, match="Image processing failed after 1 attempts"):
            provider.generate_text(
                images=["https://example.com/cat.jpg"],
                model_name="gpt-4o",
                temperature=0.7,
                max_tokens=100,
                sys_msg="You are a helpful assistant",
                prompt="What's in this image?",
                retries=1,
                config={},
            )
