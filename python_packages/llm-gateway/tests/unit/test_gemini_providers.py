"""Unit tests for Gemini providers using mocking."""

import pytest
from unittest.mock import Mock, patch

from llm_gateway.models.text_generation.gemini import GeminiTextGenerationProvider
from llm_gateway.models.embeddings.gemini import GeminiEmbeddingProvider
from llm_gateway.models.vision.gemini import GeminiVisionProvider
from llm_gateway.models.embeddings.core.interfaces import EmbeddingInfo, EmbeddingType


class TestGeminiTextGenerationProvider:
    """Unit tests for GeminiTextGenerationProvider"""

    def test_generate_text_success(self):
        """Test successful text generation"""
        # Create mock response
        mock_response = Mock()
        mock_response.text = "This is a test response from Gemini"
        mock_response.function_calls = None  # Important: must be None, not a Mock
        mock_response.input_tokens = 10
        mock_response.output_tokens = 5

        provider = GeminiTextGenerationProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(return_value=mock_response)

        result = provider.generate_text(
            model_name="gemini-1.5-flash",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="Hello",
            retries=1,
            config={},
        )

        assert result.text == "This is a test response from Gemini"
        assert result.tokens_in == 10
        assert result.tokens_out == 5
        assert result.latency > 0
        assert result.tool_calls is None

    def test_generate_text_with_tools(self):
        """Test text generation with tool calls"""
        # Create mock function call
        mock_function_call = Mock()
        mock_function_call.name = "get_weather"
        mock_function_call.args = {"location": "NYC"}

        # Create mock response with function_calls attribute
        mock_response = Mock()
        mock_response.text = ""
        mock_response.function_calls = [mock_function_call]  # List of function calls
        mock_response.input_tokens = 20
        mock_response.output_tokens = 10

        provider = GeminiTextGenerationProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(return_value=mock_response)

        result = provider.generate_text(
            model_name="gemini-1.5-flash",
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

    def test_generate_text_with_messages(self):
        """Test text generation with message history"""
        mock_response = Mock()
        mock_response.text = "I remember our previous conversation"
        mock_response.function_calls = None
        mock_response.input_tokens = 30
        mock_response.output_tokens = 8

        provider = GeminiTextGenerationProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(return_value=mock_response)

        result = provider.generate_text(
            model_name="gemini-1.5-flash",
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
        provider = GeminiTextGenerationProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(side_effect=Exception("API Error"))

        with pytest.raises(RuntimeError, match="Text generation failed after 1 attempts"):
            provider.generate_text(
                model_name="gemini-1.5-flash",
                temperature=0.7,
                max_tokens=100,
                sys_msg="You are a helpful assistant",
                prompt="Hello",
                retries=1,
                config={},
            )

    def test_stream_text_not_implemented(self):
        """Test that streaming raises NotImplementedError"""
        provider = GeminiTextGenerationProvider(api_key="test-key")

        with pytest.raises(NotImplementedError, match="Streaming not implemented"):
            provider.stream_text(
                model_name="gemini-1.5-flash",
                temperature=0.7,
                max_tokens=100,
                sys_msg="You are a helpful assistant",
                prompt="Hello",
                retries=1,
                config={},
            )


class TestGeminiEmbeddingProvider:
    """Unit tests for GeminiEmbeddingProvider"""

    def test_embed_documents_success(self):
        """Test successful document embedding"""
        mock_response = Mock()
        mock_response.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        provider = GeminiEmbeddingProvider(api_key="test-key")
        provider.client.models.embed_content = Mock(return_value=mock_response)

        info = EmbeddingInfo(type=EmbeddingType.GEMINI, name="text-embedding-004")
        result = provider.embed_documents(texts=["Hello world"], info=info)

        assert len(result.embeddings) == 1
        assert result.embeddings[0] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert result.tokens_in > 0
        assert result.latency > 0

    def test_embed_documents_multiple(self):
        """Test embedding multiple documents"""
        mock_response1 = Mock()
        mock_response1.embedding = [0.1, 0.2, 0.3]

        mock_response2 = Mock()
        mock_response2.embedding = [0.4, 0.5, 0.6]

        provider = GeminiEmbeddingProvider(api_key="test-key")
        provider.client.models.embed_content = Mock(side_effect=[mock_response1, mock_response2])

        info = EmbeddingInfo(type=EmbeddingType.GEMINI, name="text-embedding-004")
        result = provider.embed_documents(texts=["First doc", "Second doc"], info=info)

        assert len(result.embeddings) == 2
        assert result.embeddings[0] == [0.1, 0.2, 0.3]
        assert result.embeddings[1] == [0.4, 0.5, 0.6]
        assert result.tokens_in > 0

    def test_embed_documents_api_error(self):
        """Test handling of API errors"""
        provider = GeminiEmbeddingProvider(api_key="test-key")
        provider.client.models.embed_content = Mock(side_effect=Exception("API Error"))

        info = EmbeddingInfo(type=EmbeddingType.GEMINI, name="text-embedding-004")

        with pytest.raises(RuntimeError, match="Failed to embed text after 5 retries"):
            provider.embed_documents(texts=["Hello world"], info=info)


class TestGeminiVisionProvider:
    """Unit tests for GeminiVisionProvider"""

    @patch("llm_gateway.models.vision.gemini.httpx.get")
    def test_generate_text_success(self, mock_httpx_get):
        """Test successful image processing"""
        # Mock httpx response for image fetching
        mock_http_response = Mock()
        mock_http_response.content = b"fake_image_data"
        mock_http_response.raise_for_status = Mock()
        mock_httpx_get.return_value = mock_http_response

        # Mock Gemini API response
        mock_response = Mock()
        mock_response.text = "This image shows a cat"
        mock_response.input_tokens = 100
        mock_response.output_tokens = 10

        provider = GeminiVisionProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(return_value=mock_response)

        result = provider.generate_text(
            images=["https://example.com/cat.jpg"],
            model_name="gemini-1.5-pro",
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

    @patch("llm_gateway.models.vision.gemini.httpx.get")
    def test_generate_text_multiple_images(self, mock_httpx_get):
        """Test processing multiple images"""
        # Mock httpx response for image fetching
        mock_http_response = Mock()
        mock_http_response.content = b"fake_image_data"
        mock_http_response.raise_for_status = Mock()
        mock_httpx_get.return_value = mock_http_response

        # Mock Gemini API response
        mock_response = Mock()
        mock_response.text = "The first image shows a cat, the second shows a dog"
        mock_response.input_tokens = 200
        mock_response.output_tokens = 15

        provider = GeminiVisionProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(return_value=mock_response)

        result = provider.generate_text(
            images=["https://example.com/cat.jpg", "https://example.com/dog.jpg"],
            model_name="gemini-1.5-pro",
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

    def test_generate_text_with_bytes(self):
        """Test processing images provided as bytes"""
        # Mock Gemini API response
        mock_response = Mock()
        mock_response.text = "This image shows a cat"
        mock_response.input_tokens = 100
        mock_response.output_tokens = 10

        provider = GeminiVisionProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(return_value=mock_response)

        result = provider.generate_text(
            images=[b"fake_image_bytes"],
            model_name="gemini-1.5-pro",
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

    def test_generate_text_api_error(self):
        """Test handling of API errors"""
        provider = GeminiVisionProvider(api_key="test-key")
        provider.client.models.generate_content = Mock(side_effect=Exception("API Error"))

        with pytest.raises(RuntimeError, match="Image processing failed after 1 attempts"):
            provider.generate_text(
                images=[b"fake_image_bytes"],
                model_name="gemini-1.5-pro",
                temperature=0.7,
                max_tokens=100,
                sys_msg="You are a helpful assistant",
                prompt="What's in this image?",
                retries=1,
                config={},
            )
