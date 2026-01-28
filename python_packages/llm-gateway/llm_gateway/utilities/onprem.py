import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv()

ONPREM_GET_MODELS_ENDPOINT = os.getenv("ONPREM_GET_MODELS_ENDPOINT")
ONPREM_BASE_MODEL_URL = os.getenv("ONPREM_BASE_MODEL_URL")
ONPREM_USER = os.getenv("ONPREM_USER")
ONPREM_SECRET = os.getenv("ONPREM_SECRET")


def get_model_endpoint(model_name: str) -> str:
    assert ONPREM_GET_MODELS_ENDPOINT, "ONPREM_GET_MODELS_ENDPOINT must be set"
    assert ONPREM_USER, "ONPREM_USER must be set"
    assert ONPREM_SECRET, "ONPREM_SECRET must be set"

    headers = {"Content-Type": "application/json"}
    auth_value = base64.b64encode(f"{ONPREM_USER}:{ONPREM_SECRET}".encode()).decode(
        "utf-8"
    )
    headers["Authorization"] = f"Basic {auth_value}"

    response = requests.get(ONPREM_GET_MODELS_ENDPOINT, headers=headers, timeout=10)
    response.raise_for_status()

    json_response = response.json()
    for model in json_response:
        print(model)
        if (
            model.get("status_description") == "Endpoint is running."
            and model_name.lower() in model.get("endpoint_name").lower()
        ):
            base_url = f"{ONPREM_BASE_MODEL_URL}{model.get('url')}"
            if model.get("task") == "image-text-to-text":
                return f"{base_url}/image_infer"
            return f"{base_url}/infer"

    raise Exception(f"Model: [{model_name}] is unavailable.")
