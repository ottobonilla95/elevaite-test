"""Unit tests for Bedrock providers using botocore mocking."""

import json
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from llm_gateway.models.text_generation.bedrock import BedrockTextGenerationProvider
from llm_gateway.models.embeddings.bedrock import BedrockEmbeddingProvider
from llm_gateway.models.vision.bedrock import BedrockVisionProvider
from llm_gateway.models.embeddings.core.interfaces import EmbeddingInfo, EmbeddingType


class TestBedrockTextGenerationProvider:
    """Unit tests for BedrockTextGenerationProvider"""

    @patch("botocore.client.BaseClient._make_api_call")
    def test_generate_text_legacy_api_success(self, mock_make_api_call):
        """Test successful text generation using legacy API (non-tool-supporting model)"""
        # Mock InvokeModel response
        mock_response = {
            "body": Mock(
                read=lambda: json.dumps(
                    {
                        "completion": "This is a test response from Bedrock",
                        "input_tokens": 10,
                        "output_tokens": 5,
                    }
                ).encode()
            )
        }
        mock_make_api_call.return_value = mock_response

        provider = BedrockTextGenerationProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        result = provider.generate_text(
            model_name="anthropic.claude-instant-v1",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="Hello",
            retries=1,
            config={},
        )

        assert result.text == "This is a test response from Bedrock"
        assert result.tokens_in == 10
        assert result.tokens_out == 5
        assert result.latency > 0

    @patch("botocore.client.BaseClient._make_api_call")
    def test_generate_text_converse_api_success(self, mock_make_api_call):
        """Test successful text generation using Converse API (tool-supporting model)"""
        # Mock Converse response
        mock_response = {
            "output": {
                "message": {
                    "content": [{"text": "This is a test response from Claude 3"}],
                    "role": "assistant",
                }
            },
            "usage": {"inputTokens": 10, "outputTokens": 5},
            "stopReason": "end_turn",
        }
        mock_make_api_call.return_value = mock_response

        provider = BedrockTextGenerationProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        result = provider.generate_text(
            model_name="anthropic.claude-3-5-sonnet-20240620-v1:0",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="Hello",
            retries=1,
            config={},
        )

        assert result.text == "This is a test response from Claude 3"
        assert result.tokens_in == 10
        assert result.tokens_out == 5
        assert result.latency > 0
        assert result.finish_reason == "end_turn"

    @patch("botocore.client.BaseClient._make_api_call")
    def test_generate_text_with_tools(self, mock_make_api_call):
        """Test text generation with tool calls"""
        # Mock Converse response with tool use
        mock_response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "call_123",
                                "name": "get_weather",
                                "input": {"location": "NYC"},
                            }
                        }
                    ],
                    "role": "assistant",
                }
            },
            "usage": {"inputTokens": 20, "outputTokens": 10},
            "stopReason": "tool_use",
        }
        mock_make_api_call.return_value = mock_response

        provider = BedrockTextGenerationProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        result = provider.generate_text(
            model_name="anthropic.claude-3-5-sonnet-20240620-v1:0",
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

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == {"location": "NYC"}
        assert result.finish_reason == "tool_use"

    @patch("botocore.client.BaseClient._make_api_call")
    def test_generate_text_api_error(self, mock_make_api_call):
        """Test handling of API errors"""
        mock_make_api_call.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid request"}},
            "InvokeModel",
        )

        provider = BedrockTextGenerationProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        with pytest.raises(
            RuntimeError, match="Text generation failed after 1 attempts"
        ):
            provider.generate_text(
                model_name="anthropic.claude-instant-v1",
                temperature=0.7,
                max_tokens=100,
                sys_msg="You are a helpful assistant",
                prompt="Hello",
                retries=1,
                config={},
            )


class TestBedrockEmbeddingProvider:
    """Unit tests for BedrockEmbeddingProvider"""

    @patch("botocore.client.BaseClient._make_api_call")
    def test_embed_documents_success(self, mock_make_api_call):
        """Test successful document embedding"""
        # Mock InvokeModel response - Bedrock expects "completion" key
        # The text_to_embedding method converts text to embedding
        mock_response = {
            "body": Mock(read=lambda: json.dumps({"completion": "test"}).encode())
        }
        mock_make_api_call.return_value = mock_response

        provider = BedrockEmbeddingProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        info = EmbeddingInfo(
            type=EmbeddingType.BEDROCK, name="amazon.titan-embed-text-v1"
        )
        result = provider.embed_documents(texts=["Hello world"], info=info)

        assert len(result.embeddings) == 1
        # text_to_embedding converts "test" to [116.0, 101.0, 115.0, 116.0] (ord of each char)
        assert result.embeddings[0] == [116.0, 101.0, 115.0, 116.0]
        assert result.tokens_in > 0
        assert result.latency > 0

    @patch("botocore.client.BaseClient._make_api_call")
    def test_embed_documents_multiple(self, mock_make_api_call):
        """Test embedding multiple documents"""
        # Mock InvokeModel responses
        mock_response1 = {
            "body": Mock(read=lambda: json.dumps({"completion": "abc"}).encode())
        }
        mock_response2 = {
            "body": Mock(read=lambda: json.dumps({"completion": "def"}).encode())
        }
        mock_make_api_call.side_effect = [mock_response1, mock_response2]

        provider = BedrockEmbeddingProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        info = EmbeddingInfo(
            type=EmbeddingType.BEDROCK, name="amazon.titan-embed-text-v1"
        )
        result = provider.embed_documents(texts=["First doc", "Second doc"], info=info)

        assert len(result.embeddings) == 2
        # "abc" -> [97.0, 98.0, 99.0], "def" -> [100.0, 101.0, 102.0]
        assert result.embeddings[0] == [97.0, 98.0, 99.0]
        assert result.embeddings[1] == [100.0, 101.0, 102.0]
        assert result.tokens_in > 0

    @patch("botocore.client.BaseClient._make_api_call")
    def test_embed_documents_api_error(self, mock_make_api_call):
        """Test handling of API errors"""
        mock_make_api_call.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid request"}},
            "InvokeModel",
        )

        provider = BedrockEmbeddingProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        info = EmbeddingInfo(
            type=EmbeddingType.BEDROCK, name="amazon.titan-embed-text-v1"
        )

        with pytest.raises(
            RuntimeError, match="Embedding generation failed due to unexpected error"
        ):
            provider.embed_documents(texts=["Hello world"], info=info)


class TestBedrockVisionProvider:
    """Unit tests for BedrockVisionProvider"""

    @patch("botocore.client.BaseClient._make_api_call")
    def test_generate_text_success(self, mock_make_api_call):
        """Test successful image processing"""
        # Mock InvokeModel response (vision uses legacy API, not Converse)
        mock_response = {
            "body": Mock(
                read=lambda: json.dumps(
                    {
                        "type": "message",
                        "content": [{"type": "text", "text": "This image shows a cat"}],
                        "usage": {"input_tokens": 100, "output_tokens": 10},
                    }
                ).encode()
            )
        }
        mock_make_api_call.return_value = mock_response

        provider = BedrockVisionProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        result = provider.generate_text(
            images=[b"fake_image_bytes"],
            model_name="anthropic.claude-3-5-sonnet-20240620-v1:0",
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

    @patch("llm_gateway.models.vision.bedrock.httpx.get")
    @patch("botocore.client.BaseClient._make_api_call")
    def test_generate_text_with_url(self, mock_make_api_call, mock_httpx_get):
        """Test processing image from URL"""
        # Mock httpx response
        mock_http_response = Mock()
        mock_http_response.content = b"fake_image_data"
        mock_http_response.raise_for_status = Mock()
        mock_httpx_get.return_value = mock_http_response

        # Mock InvokeModel response
        mock_response = {
            "body": Mock(
                read=lambda: json.dumps(
                    {
                        "type": "message",
                        "content": [{"type": "text", "text": "This image shows a dog"}],
                        "usage": {"input_tokens": 100, "output_tokens": 10},
                    }
                ).encode()
            )
        }
        mock_make_api_call.return_value = mock_response

        provider = BedrockVisionProvider(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-west-1",
        )

        result = provider.generate_text(
            images=["https://example.com/dog.jpg"],
            model_name="anthropic.claude-3-5-sonnet-20240620-v1:0",
            temperature=0.7,
            max_tokens=100,
            sys_msg="You are a helpful assistant",
            prompt="What's in this image?",
            retries=1,
            config={},
        )

        assert result.text == "This image shows a dog"
        assert result.tokens_in == 100
        assert result.tokens_out == 10
