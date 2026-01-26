"""
Unit tests for LLM Gateway services

Tests TextGenerationService, EmbeddingService, VisionService, and UniversalService
with mocked providers to avoid external API calls.
"""

import pytest
from unittest.mock import MagicMock, patch

from llm_gateway.services import (
    TextGenerationService,
    EmbeddingService,
    VisionService,
    UniversalService,
    RequestType,
)
from llm_gateway.models.text_generation.core.interfaces import TextGenerationResponse, ToolCall
from llm_gateway.models.text_generation.core.base import BaseTextGenerationProvider
from llm_gateway.models.embeddings.core.interfaces import EmbeddingResponse, EmbeddingRequest, EmbeddingInfo, EmbeddingType
from llm_gateway.models.embeddings.core.base import BaseEmbeddingProvider
from llm_gateway.models.vision.core.base import BaseVisionProvider
from llm_gateway.models.provider import ModelProviderFactory


@pytest.fixture
def mock_factory():
    """Create a mock ModelProviderFactory"""
    return MagicMock(spec=ModelProviderFactory)


@pytest.fixture
def mock_text_provider():
    """Create a mock text generation provider"""
    provider = MagicMock(spec=BaseTextGenerationProvider)
    provider.generate_text.return_value = TextGenerationResponse(
        text="Generated text",
        latency=0.5,
        tokens_in=10,
        tokens_out=5,
        model_name="test-model",
        tool_calls=None,
    )
    provider.stream_text.return_value = iter(
        [
            {"type": "delta", "text": "Hello"},
            {"type": "delta", "text": " world"},
            {"type": "final", "response": {"text": "Hello world"}},
        ]
    )
    return provider


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider"""
    provider = MagicMock(spec=BaseEmbeddingProvider)
    provider.embed_documents.return_value = EmbeddingResponse(
        latency=0.3,
        embeddings=[[0.1, 0.2, 0.3]],
        tokens_in=5,
    )
    return provider


@pytest.fixture
def mock_vision_provider():
    """Create a mock vision provider"""
    provider = MagicMock(spec=BaseVisionProvider)
    provider.generate_text.return_value = TextGenerationResponse(
        text="Image description",
        latency=0.7,
        tokens_in=15,
        tokens_out=8,
        model_name="vision-model",
        tool_calls=None,
    )
    return provider


class TestTextGenerationService:
    """Tests for TextGenerationService"""

    def test_initialization_with_factory(self, mock_factory):
        """Test service initialization with provided factory"""
        service = TextGenerationService(factory=mock_factory)
        assert service.factory == mock_factory

    def test_initialization_without_factory(self):
        """Test service initialization creates default factory"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = TextGenerationService()
            assert service.factory is not None

    def test_generate_text_success(self, mock_factory, mock_text_provider):
        """Test successful text generation"""
        mock_factory.get_provider.return_value = mock_text_provider
        service = TextGenerationService(factory=mock_factory)

        config = {"type": "openai"}
        result = service.generate(
            prompt="Test prompt",
            config=config,
            max_tokens=100,
            model_name="gpt-4",
            sys_msg="You are helpful",
            temperature=0.7,
        )

        assert result.text == "Generated text"
        assert result.latency == 0.5
        mock_factory.get_provider.assert_called_once_with("openai")
        mock_text_provider.generate_text.assert_called_once()

    def test_generate_with_tools(self, mock_factory, mock_text_provider):
        """Test text generation with tool calls"""
        tool_call = ToolCall(
            id="call_123",
            name="get_weather",
            arguments={"location": "NYC"},
        )
        mock_text_provider.generate_text.return_value = TextGenerationResponse(
            text="",
            latency=0.5,
            tokens_in=10,
            tokens_out=5,
            model_name="test-model",
            tool_calls=[tool_call],
        )
        mock_factory.get_provider.return_value = mock_text_provider
        service = TextGenerationService(factory=mock_factory)

        tools = [{"type": "function", "function": {"name": "get_weather"}}]
        result = service.generate(
            prompt="What's the weather?",
            config={"type": "openai"},
            tools=tools,
            tool_choice="auto",
        )

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_weather"

    def test_generate_with_messages(self, mock_factory, mock_text_provider):
        """Test text generation with message history"""
        mock_factory.get_provider.return_value = mock_text_provider
        service = TextGenerationService(factory=mock_factory)

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = service.generate(
            prompt="How are you?",
            config={"type": "openai"},
            messages=messages,
        )

        assert result.text == "Generated text"
        call_kwargs = mock_text_provider.generate_text.call_args[1]
        assert call_kwargs["messages"] == messages

    def test_generate_provider_error(self, mock_factory, mock_text_provider):
        """Test error handling when provider fails"""
        mock_text_provider.generate_text.side_effect = Exception("API Error")
        mock_factory.get_provider.return_value = mock_text_provider
        service = TextGenerationService(factory=mock_factory)

        with pytest.raises(RuntimeError, match="Error in text generation"):
            service.generate(prompt="Test", config={"type": "openai"})

    def test_generate_invalid_provider_type(self, mock_factory):
        """Test error when provider is not a text generation provider"""
        mock_factory.get_provider.return_value = MagicMock()  # Not a BaseTextGenerationProvider
        service = TextGenerationService(factory=mock_factory)

        with pytest.raises(RuntimeError, match="Error in text generation"):
            service.generate(prompt="Test", config={"type": "invalid"})

    def test_stream_text_success(self, mock_factory, mock_text_provider):
        """Test streaming text generation"""
        mock_text_provider.stream_text.return_value = iter(
            [
                {"type": "delta", "text": "Hello"},
                {"type": "delta", "text": " world"},
                {"type": "final", "response": {"text": "Hello world"}},
            ]
        )
        mock_factory.get_provider.return_value = mock_text_provider
        service = TextGenerationService(factory=mock_factory)

        events = list(service.stream(prompt="Test", config={"type": "openai"}))

        assert len(events) == 3
        assert events[0]["type"] == "delta"
        assert events[2]["type"] == "final"

    def test_stream_provider_error(self, mock_factory, mock_text_provider):
        """Test error handling in streaming"""
        mock_text_provider.stream_text.side_effect = Exception("Stream error")
        mock_factory.get_provider.return_value = mock_text_provider
        service = TextGenerationService(factory=mock_factory)

        with pytest.raises(RuntimeError, match="Error in text generation streaming"):
            list(service.stream(prompt="Test", config={"type": "openai"}))


class TestEmbeddingService:
    """Tests for EmbeddingService"""

    def test_initialization_with_factory(self, mock_factory):
        """Test service initialization with provided factory"""
        service = EmbeddingService(factory=mock_factory)
        assert service.factory == mock_factory

    def test_embed_documents_success(self, mock_factory, mock_embedding_provider):
        """Test successful document embedding"""
        mock_factory.get_provider.return_value = mock_embedding_provider
        service = EmbeddingService(factory=mock_factory)

        request = EmbeddingRequest(
            texts=["Hello world", "Test document"],
            info=EmbeddingInfo(type=EmbeddingType.OPENAI, name="text-embedding-3-small"),
        )
        result = service.embed(request)

        assert result.latency == 0.3
        assert len(result.embeddings) == 1
        mock_factory.get_provider.assert_called_once_with(EmbeddingType.OPENAI)
        mock_embedding_provider.embed_documents.assert_called_once()

    def test_embed_provider_error(self, mock_factory, mock_embedding_provider):
        """Test error handling when embedding fails"""
        mock_embedding_provider.embed_documents.side_effect = Exception("Embedding error")
        mock_factory.get_provider.return_value = mock_embedding_provider
        service = EmbeddingService(factory=mock_factory)

        request = EmbeddingRequest(
            texts=["Test"],
            info=EmbeddingInfo(type=EmbeddingType.OPENAI, name="test-model"),
        )

        with pytest.raises(RuntimeError, match="Error in embedding"):
            service.embed(request)

    def test_embed_invalid_provider_type(self, mock_factory):
        """Test error when provider is not an embedding provider"""
        mock_factory.get_provider.return_value = MagicMock()  # Not a BaseEmbeddingProvider
        service = EmbeddingService(factory=mock_factory)

        request = EmbeddingRequest(
            texts=["Test"],
            info=EmbeddingInfo(type=EmbeddingType.OPENAI, name="test"),
        )

        with pytest.raises(RuntimeError, match="Error in embedding"):
            service.embed(request)


class TestVisionService:
    """Tests for VisionService"""

    def test_initialization_with_factory(self, mock_factory):
        """Test service initialization with provided factory"""
        service = VisionService(factory=mock_factory)
        assert service.factory == mock_factory

    def test_process_images_success(self, mock_factory, mock_vision_provider):
        """Test successful image processing"""
        mock_factory.get_provider.return_value = mock_vision_provider
        service = VisionService(factory=mock_factory)

        result = service.process_images(
            prompt="Describe this image",
            images=["base64_image_data"],
            config={"type": "openai"},
            max_tokens=100,
            model_name="gpt-4-vision",
        )

        assert result.text == "Image description"
        assert result.latency == 0.7
        mock_factory.get_provider.assert_called_once_with("openai")
        mock_vision_provider.generate_text.assert_called_once()

    def test_process_multiple_images(self, mock_factory, mock_vision_provider):
        """Test processing multiple images"""
        mock_factory.get_provider.return_value = mock_vision_provider
        service = VisionService(factory=mock_factory)

        images = ["image1_base64", "image2_base64", "image3_base64"]
        result = service.process_images(
            prompt="Compare these images",
            images=images,
            config={"type": "openai"},
        )

        assert result.text == "Image description"
        call_kwargs = mock_vision_provider.generate_text.call_args[1]
        assert call_kwargs["images"] == images

    def test_process_images_provider_error(self, mock_factory, mock_vision_provider):
        """Test error handling when vision processing fails"""
        mock_vision_provider.generate_text.side_effect = Exception("Vision error")
        mock_factory.get_provider.return_value = mock_vision_provider
        service = VisionService(factory=mock_factory)

        with pytest.raises(RuntimeError, match="Error in processing images"):
            service.process_images(
                prompt="Test",
                images=["image"],
                config={"type": "openai"},
            )

    def test_process_images_invalid_provider_type(self, mock_factory):
        """Test error when provider is not a vision provider"""
        mock_factory.get_provider.return_value = MagicMock()  # Not a BaseVisionProvider
        service = VisionService(factory=mock_factory)

        with pytest.raises(RuntimeError, match="Error in processing images"):
            service.process_images(
                prompt="Test",
                images=["image"],
                config={"type": "invalid"},
            )


class TestUniversalService:
    """Tests for UniversalService"""

    def test_initialization(self):
        """Test service initialization"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = UniversalService()
            assert service.factory is not None

    def test_handle_embedding_request(self, mock_embedding_provider):
        """Test routing embedding request to correct provider"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = UniversalService()
            service.factory.get_provider = MagicMock(return_value=mock_embedding_provider)

            result = service.handle_request(
                request_type=RequestType.EMBEDDING,
                provider_type=EmbeddingType.OPENAI,
                texts=["Test text"],
                info=EmbeddingInfo(type=EmbeddingType.OPENAI, name="test-model"),
            )

            assert result.latency == 0.3
            mock_embedding_provider.embed_documents.assert_called_once()

    def test_handle_text_generation_request(self, mock_text_provider):
        """Test routing text generation request to correct provider"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = UniversalService()
            service.factory.get_provider = MagicMock(return_value=mock_text_provider)

            result = service.handle_request(
                request_type=RequestType.TEXT_GENERATION,
                provider_type="openai",
                prompt="Test prompt",
                config={"type": "openai"},
                max_tokens=100,
            )

            assert result.text == "Generated text"
            mock_text_provider.generate_text.assert_called_once()

    def test_handle_vision_request(self, mock_vision_provider):
        """Test routing vision request to correct provider"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = UniversalService()
            service.factory.get_provider = MagicMock(return_value=mock_vision_provider)

            result = service.handle_request(
                request_type=RequestType.VISION,
                provider_type="openai",
                prompt="Describe image",
                images=["image_data"],
                config={"type": "openai"},
            )

            assert result.text == "Image description"
            mock_vision_provider.generate_text.assert_called_once()

    def test_handle_embedding_invalid_provider(self):
        """Test error when embedding provider is wrong type"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = UniversalService()
            service.factory.get_provider = MagicMock(return_value=MagicMock())  # Wrong type

            with pytest.raises(RuntimeError, match="not a BaseEmbeddingProvider"):
                service.handle_request(
                    request_type=RequestType.EMBEDDING,
                    provider_type=EmbeddingType.OPENAI,
                    texts=["Test"],
                    info=EmbeddingInfo(type=EmbeddingType.OPENAI, name="test"),
                )

    def test_handle_text_generation_invalid_provider(self):
        """Test error when text generation provider is wrong type"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = UniversalService()
            service.factory.get_provider = MagicMock(return_value=MagicMock())  # Wrong type

            with pytest.raises(RuntimeError, match="not a BaseTextGenerationProvider"):
                service.handle_request(
                    request_type=RequestType.TEXT_GENERATION,
                    provider_type="openai",
                    prompt="Test",
                    config={"type": "openai"},
                )

    def test_handle_vision_invalid_provider(self):
        """Test error when vision provider is wrong type"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = UniversalService()
            service.factory.get_provider = MagicMock(return_value=MagicMock())  # Wrong type

            with pytest.raises(RuntimeError, match="not a BaseVisionProvider"):
                service.handle_request(
                    request_type=RequestType.VISION,
                    provider_type="openai",
                    prompt="Test",
                    images=["image"],
                    config={"type": "openai"},
                )
