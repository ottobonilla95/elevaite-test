import logging
import base64

from llm_gateway.models.vision.core.interfaces import VisionType
from llm_gateway.services import VisionService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Retrieved from https://picsum.photos/200
# Requires valid placeholders for Gemini
PUBLIC_IMAGE_URL = "https://fastly.picsum.photos/id/547/200/200.jpg?hmac=04fFD0MMF_hIH8HFysMTH_z8R7CwblctCIrBpdzouJs"
PUBLIC_IMAGE_URL_2 = "https://fastly.picsum.photos/id/841/200/200.jpg?hmac=jAPzaXgN_B37gVuIQvmtuRCmYEC0lJP86OZexH1yam4"

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
        PUBLIC_IMAGE_URL_2,
    ]
    response = service.process_images("Describe what this image shows", images, config)

    assert isinstance(response, str)
    assert len(response) > 0
    logger.info(f"OpenAI Response for Multiple Images: {response}")


def test_gemini_process_base64_image(model_provider_factory):
    """
    Test Gemini image-to-text service with a Base64 image.
    """
    service = VisionService(model_provider_factory)

    config = {
        "type": VisionType.GEMINI,
        "model": "gemini-1.5-pro",
        "max_tokens": 300,
        "prompt": "What is in this image?",
    }

    response = service.process_images(
        "Describe what this image shows.", [MOCK_IMAGE_BYTES], config
    )

    assert isinstance(response, str)
    assert len(response) > 0
    logger.info(f"Gemini Response for Base64 Image: {response}")


def test_gemini_process_image_url(model_provider_factory):
    """
    Test Gemini image-to-text service with an image URL.
    """
    service = VisionService(model_provider_factory)
    config = {
        "type": VisionType.GEMINI,
        "model": "gemini-1.5-pro",
        "max_tokens": 300,
        "prompt": "What is in this image?",
    }

    response = service.process_images(
        "Describe what this image shows.", [PUBLIC_IMAGE_URL], config
    )

    assert isinstance(response, str)
    assert len(response) > 0
    logger.info(f"Gemini Response for Image URL: {response}")


def test_gemini_process_multiple_images(model_provider_factory):
    """
    Test Gemini image-to-text service with multiple images (Base64 and URLs).
    """
    service = VisionService(model_provider_factory)

    config = {
        "type": VisionType.GEMINI,
        "model": "gemini-1.5-pro",
        "max_tokens": 300,
        "prompt": "What is in these images?",
    }

    images = [
        MOCK_IMAGE_BYTES,
        PUBLIC_IMAGE_URL,
        PUBLIC_IMAGE_URL_2,
    ]
    response = service.process_images("Describe what these images show", images, config)

    assert isinstance(response, str)
    assert len(response) > 0
    logger.info(f"Gemini Response for Multiple Images: {response}")
