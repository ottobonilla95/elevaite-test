import logging
import base64

from llm_gateway.models.text_generation.core.interfaces import TextGenerationResponse
from llm_gateway.models.vision.core.interfaces import VisionType
from llm_gateway.services import RequestType, UniversalService

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


def validate_and_log_response(
    response: TextGenerationResponse, vision_type: VisionType, test_case: str
):
    """
    Validate the response from the current Vision service and log relevant details.
    """
    assert isinstance(
        response, TextGenerationResponse
    ), "Response must be a TextGenerationResponse instance."
    assert len(response.text) > 0, "Generated text must not be empty."
    assert response.tokens_in > 0, "Input token count must be greater than 0."
    assert response.tokens_out > 0, "Output token count must be greater than 0."

    logger.info(
        f"{vision_type.name} Response for {test_case}: {response.text}\n"
        f"Tokens In: {response.tokens_in}, Tokens Out: {response.tokens_out}, Latency: {response.latency:.2f}s"
    )


def test_openai_process_base64_image(model_provider_factory, fake_prompt):
    """
    Test OpenAI image-to-text service with a Base64 image using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        prompt=fake_prompt,
        provider_type=VisionType.OPENAI,
        images=[MOCK_IMAGE_BYTES],
    )

    validate_and_log_response(response, VisionType.OPENAI, "Image URL")


def test_openai_process_image_url(model_provider_factory, fake_prompt):
    """
    Test OpenAI image-to-text service with an image URL using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.OPENAI,
        prompt=fake_prompt,
        images=[PUBLIC_IMAGE_URL],
    )
    validate_and_log_response(response, VisionType.OPENAI, "Image URL")


def test_openai_process_multiple_images(model_provider_factory, fake_prompt):
    """
    Test OpenAI image-to-text service with multiple images (Base64 and URLs) using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    images = [
        MOCK_IMAGE_BYTES,
        PUBLIC_IMAGE_URL,
        PUBLIC_IMAGE_URL_2,
    ]
    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.OPENAI,
        prompt=fake_prompt,
        images=images,
    )

    validate_and_log_response(response, VisionType.OPENAI, "Image URL")


def test_gemini_process_base64_image(model_provider_factory, fake_prompt):
    """
    Test Gemini image-to-text service with a Base64 image using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.GEMINI,
        prompt=fake_prompt,
        images=[MOCK_IMAGE_BYTES],
    )

    validate_and_log_response(response, VisionType.GEMINI, "Image URL")


def test_gemini_process_image_url(model_provider_factory, fake_prompt):
    """
    Test Gemini image-to-text service with an image URL using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.GEMINI,
        prompt=fake_prompt,
        images=[PUBLIC_IMAGE_URL],
    )

    validate_and_log_response(response, VisionType.GEMINI, "Image URL")


def test_gemini_process_multiple_images(model_provider_factory, fake_prompt):
    """
    Test Gemini image-to-text service with multiple images (Base64 and URLs) using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    images = [
        MOCK_IMAGE_BYTES,
        PUBLIC_IMAGE_URL,
        PUBLIC_IMAGE_URL_2,
    ]
    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.GEMINI,
        prompt=fake_prompt,
        images=images,
    )

    validate_and_log_response(response, VisionType.GEMINI, "Image URL")


def test_bedrock_process_base64_image(model_provider_factory, fake_prompt):
    """
    Test Bedrock image-to-text service with a Base64 image using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.BEDROCK,
        prompt=fake_prompt,
        images=[MOCK_IMAGE_BYTES],
    )

    validate_and_log_response(response, VisionType.BEDROCK, "Image URL")


def test_bedrock_process_image_url(model_provider_factory, fake_prompt):
    """
    Test Bedrock image-to-text service with an image URL using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.BEDROCK,
        prompt=fake_prompt,
        images=[PUBLIC_IMAGE_URL],
    )

    validate_and_log_response(response, VisionType.BEDROCK, "Image URL")


def test_bedrock_process_multiple_images(model_provider_factory, fake_prompt):
    """
    Test Bedrock image-to-text service with multiple images (Base64 and URLs) using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    images = [
        MOCK_IMAGE_BYTES,
        PUBLIC_IMAGE_URL,
        PUBLIC_IMAGE_URL_2,
    ]
    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.BEDROCK,
        prompt=fake_prompt,
        images=images,
    )

    validate_and_log_response(response, VisionType.BEDROCK, "Image URL")


def test_onprem_process_base64_image(model_provider_factory, fake_prompt):
    """
    Test On-Prem image-to-text service with a Base64 image using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.ON_PREM,
        prompt=fake_prompt,
        images=[MOCK_IMAGE_BYTES],
    )

    validate_and_log_response(response, VisionType.ON_PREM, "Base64 Image")


def test_onprem_process_image_url(model_provider_factory, fake_prompt):
    """
    Test On-Prem image-to-text service with an image URL using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.ON_PREM,
        prompt=fake_prompt,
        images=[PUBLIC_IMAGE_URL],
    )
    validate_and_log_response(response, VisionType.ON_PREM, "Image URL")


def test_onprem_process_multiple_images(model_provider_factory, fake_prompt):
    """
    Test On-Prem image-to-text service with multiple images (Base64 and URLs) using UniversalService.
    """
    service = UniversalService(model_provider_factory)

    images = [
        MOCK_IMAGE_BYTES,
        PUBLIC_IMAGE_URL,
        PUBLIC_IMAGE_URL_2,
    ]
    response = service.handle_request(
        request_type=RequestType.VISION,
        provider_type=VisionType.ON_PREM,
        prompt=fake_prompt,
        images=images,
    )

    validate_and_log_response(response, VisionType.ON_PREM, "Multiple Images")
