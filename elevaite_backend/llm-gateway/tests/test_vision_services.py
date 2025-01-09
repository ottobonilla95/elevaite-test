import logging
import base64

from llm_gateway.models.vision.core.interfaces import VisionType
from llm_gateway.services import VisionService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PUBLIC_IMAGE_URL = "https://picsum.photos/200"  # Doesn't actually require a working image link for the tests

MOCK_IMAGE_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAUA"
    "AAAFCAYAAACNbyblAAAAHElEQVQI12P4"
    "//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
)


def test_openai_process_base64_image(model_provider_factory):
    """
    Test OpenAI image-to-text service with a Base64 image.
    """
    service = VisionService(model_provider_factory)

    config = {
        "type": VisionType.OPENAI,
        "model": "gpt-4o-mini",
        "max_tokens": 300,
        "prompt": "What is in this image?",
    }

    response = service.process_images(
        "Describe what this image shows.", [MOCK_IMAGE_BYTES], config
    )

    assert isinstance(response, str)
    assert len(response) > 0
    logger.info(f"OpenAI Response for Base64 Image: {response}")


def test_openai_process_image_url(model_provider_factory):
    """
    Test OpenAI image-to-text service with an image URL.
    """
    service = VisionService(model_provider_factory)
    config = {
        "type": VisionType.OPENAI,
        "model": "gpt-4o-mini",
        "max_tokens": 300,
        "prompt": "What is in this image?",
    }

    response = service.process_images(
        "Describe what this image shows.", [PUBLIC_IMAGE_URL], config
    )

    assert isinstance(response, str)
    assert len(response) > 0
    logger.info(f"OpenAI Response for Image URL: {response}")


def test_openai_process_multiple_images(model_provider_factory):
    """
    Test OpenAI image-to-text service with multiple images (Base64 and URLs).
    """
    service = VisionService(model_provider_factory)

    config = {
        "type": VisionType.OPENAI,
        "model": "gpt-4o-mini",
        "max_tokens": 300,
        "prompt": "What is in these images?",
    }

    images = [
        MOCK_IMAGE_BYTES,
        PUBLIC_IMAGE_URL,
        "https://via.placeholder.com/200",
    ]
    response = service.process_images("Describe what this image shows", images, config)

    assert isinstance(response, str)
    assert len(response) > 0
    logger.info(f"OpenAI Response for Multiple Images: {response}")
