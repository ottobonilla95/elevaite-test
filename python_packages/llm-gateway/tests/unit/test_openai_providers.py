"""Unit tests for OpenAI providers using mocking."""

import pytest
from unittest.mock import Mock

from llm_gateway.models.text_generation.openai import OpenAITextGenerationProvider
from llm_gateway.models.embeddings.openai import OpenAIEmbeddingProvider
from llm_gateway.models.vision.openai import OpenAIVisionProvider
from llm_gateway.models.embeddings.core.interfaces import EmbeddingInfo, EmbeddingType


def _create_responses_api_mock(
    text_content="", tool_calls=None, tokens_in=10, tokens_out=5
):
    """Helper to create a mock Responses API response."""
    mock_response = Mock()
    mock_response.output = []

    # Add message output if there's text content
    if text_content:
        mock_message = Mock()
        mock_message.type = "message"
        mock_content = Mock()
        mock_content.type = "output_text"
        mock_content.text = text_content
        mock_message.content = [mock_content]
        mock_response.output.append(mock_message)

    # Add function call outputs if there are tool calls
    if tool_calls:
        for tc in tool_calls:
            mock_func_call = Mock()
            mock_func_call.type = "function_call"
            mock_func_call.id = tc.get("id", "call_123")
            mock_func_call.call_id = tc.get("id", "call_123")
            mock_func_call.name = tc.get("name", "unknown")
            mock_func_call.arguments = tc.get("arguments", "{}")
            mock_response.output.append(mock_func_call)

    # Add usage
    mock_response.usage = Mock()
    mock_response.usage.input_tokens = tokens_in
    mock_response.usage.output_tokens = tokens_out

    return mock_response


class TestOpenAITextGenerationProvider:
    """Unit tests for OpenAITextGenerationProvider (Responses API)"""

    def test_generate_text_success(self):
        """Test successful text generation with Responses API"""
        mock_response = _create_responses_api_mock(
            text_content="This is a test response",
            tokens_in=10,
            tokens_out=5,
        )

        provider = OpenAITextGenerationProvider(api_key="test-key")
        # Mock the client's responses.create method
        provider.client.responses.create = Mock(return_value=mock_response)

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
        """Test text generation with tool calls using Responses API"""
        mock_response = _create_responses_api_mock(
            text_content="",
            tool_calls=[
                {
                    "id": "call_123",
                    "name": "get_weather",
                    "arguments": '{"location": "NYC"}',
                }
            ],
            tokens_in=20,
            tokens_out=10,
        )

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.responses.create = Mock(return_value=mock_response)

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
        """Test text generation with message history using Responses API"""
        mock_response = _create_responses_api_mock(
            text_content="I remember our previous conversation",
            tokens_in=30,
            tokens_out=8,
        )

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.responses.create = Mock(return_value=mock_response)

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
        provider.client.responses.create = Mock(side_effect=Exception("API Error"))

        with pytest.raises(
            RuntimeError, match="Text generation failed after 1 attempts"
        ):
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
        """Test successful streaming text generation with Responses API"""
        # Create mock stream events for Responses API
        mock_event1 = Mock()
        mock_event1.type = "response.output_text.delta"
        mock_event1.delta = "Hello"

        mock_event2 = Mock()
        mock_event2.type = "response.output_text.delta"
        mock_event2.delta = " world"

        mock_event3 = Mock()
        mock_event3.type = "response.completed"
        mock_event3.response = Mock()
        mock_event3.response.usage = Mock()
        mock_event3.response.usage.input_tokens = 10
        mock_event3.response.usage.output_tokens = 5

        # Create a context manager mock for streaming
        mock_stream = Mock()
        mock_stream.__enter__ = Mock(
            return_value=iter([mock_event1, mock_event2, mock_event3])
        )
        mock_stream.__exit__ = Mock(return_value=False)

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.responses.create = Mock(return_value=mock_stream)

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
        assert len(delta_chunks) == 2
        assert delta_chunks[0]["text"] == "Hello"
        assert delta_chunks[1]["text"] == " world"

    def test_generate_text_with_file_search_config(self):
        """Test text generation with file_search tool configuration"""
        mock_response = _create_responses_api_mock(
            text_content="Based on the document, the answer is...",
            tokens_in=50,
            tokens_out=20,
        )

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.responses.create = Mock(return_value=mock_response)

        result = provider.generate_text(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="What does the document say?",
            retries=1,
            config={
                "file_search": {
                    "vector_store_ids": ["vs_123"],
                    "max_num_results": 5,
                }
            },
        )

        assert result.text == "Based on the document, the answer is..."
        # Verify file_search tool was included in the API call
        call_args = provider.client.responses.create.call_args
        assert "tools" in call_args.kwargs
        tools = call_args.kwargs["tools"]
        file_search_tool = next(
            (t for t in tools if t.get("type") == "file_search"), None
        )
        assert file_search_tool is not None
        assert file_search_tool["vector_store_ids"] == ["vs_123"]

    def test_generate_text_with_files_parameter(self, tmp_path):
        """Test text generation with files parameter (auto file search)"""
        # Create a temporary test file
        test_file = tmp_path / "test_document.txt"
        test_file.write_text("This is test content for the document.")

        mock_response = _create_responses_api_mock(
            text_content="Based on the document, it says test content.",
            tokens_in=60,
            tokens_out=25,
        )

        # Mock vector store and file creation
        mock_vector_store = Mock()
        mock_vector_store.id = "vs_auto_123"

        mock_file = Mock()
        mock_file.id = "file_123"

        provider = OpenAITextGenerationProvider(api_key="test-key")
        provider.client.responses.create = Mock(return_value=mock_response)
        provider.client.vector_stores.create = Mock(return_value=mock_vector_store)
        provider.client.files.create = Mock(return_value=mock_file)
        provider.client.vector_stores.files.create = Mock()

        result = provider.generate_text(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="What does the document say?",
            retries=1,
            config={},
            files=[str(test_file)],  # Pass file path
        )

        assert result.text == "Based on the document, it says test content."
        # Verify vector store was created
        provider.client.vector_stores.create.assert_called_once()
        # Verify file was uploaded
        provider.client.files.create.assert_called_once()
        # Verify file_search tool was included in the API call
        call_args = provider.client.responses.create.call_args
        assert "tools" in call_args.kwargs
        tools = call_args.kwargs["tools"]
        file_search_tool = next(
            (t for t in tools if t.get("type") == "file_search"), None
        )
        assert file_search_tool is not None
        assert "vs_auto_123" in file_search_tool["vector_store_ids"]


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
        provider.client.embeddings.create = Mock(
            side_effect=[mock_response1, mock_response2]
        )

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
        mock_response.choices[
            0
        ].message.content = "The first image shows a cat, the second shows a dog"
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
        provider.client.chat.completions.create = Mock(
            side_effect=Exception("API Error")
        )

        with pytest.raises(
            RuntimeError, match="Image processing failed after 1 attempts"
        ):
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
