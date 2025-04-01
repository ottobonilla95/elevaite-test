import base64
import logging
import time
from typing import List

import requests


from ...utilities.onprem import get_model_endpoint
from ...utilities.tokens import count_tokens
from .core.base import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingResponse, EmbeddingType


class OnPremEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, user: str, secret: str):
        if not all([user, secret]):
            raise EnvironmentError("ONPREM_USER, and ONPREM_SECRET must be set")
        self.user = user
        self.secret = secret

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo, max_retries: int = 3
    ) -> EmbeddingResponse:
        model_name: str = info.name or "snowflake-arctic-embed-m"
        headers = {"Content-Type": "application/json"}
        auth_value = base64.b64encode(f"{self.user}:{self.secret}".encode()).decode(
            "utf-8"
        )
        headers["Authorization"] = f"Basic {auth_value}"

        payload = {
            "kwargs": {
                "sentences": texts,
            }
        }

        total_tokens = 0
        embeddings = []
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                logging.info(f"Embedding texts using model: {info.name}")
                logging.debug(f"Request Payload: {payload}")

                response = requests.post(
                    get_model_endpoint(model_name),
                    json=payload,
                    headers=headers,
                    verify=True,
                    timeout=30,
                )

                logging.debug(f"API Response Status Code: {response.status_code}")
                logging.debug(f"API Response Text: {response.text}")

                if response.status_code == 200:
                    data = response.json()
                    logging.debug(f"Full API Response Data: {data}")
                    result = data.get("result", [])

                    if isinstance(result, list) and result:
                        embeddings.extend(result)
                        total_tokens += sum(count_tokens([text]) for text in texts)
                        break
                    else:
                        raise ValueError(
                            "Unexpected response format: No 'result' found."
                        )
                else:
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {response.text}"
                    )
                    if attempt == max_retries - 1:
                        raise RuntimeError(
                            f"Embedding failed after {max_retries} attempts: {response.text}"
                        )

                time.sleep(2 ** (attempt + 1))

            except requests.exceptions.RequestException as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying..."
                )
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Embedding failed after {max_retries} attempts: {e}"
                    )
                time.sleep(2 ** (attempt + 1))

        latency = time.time() - start_time
        return EmbeddingResponse(
            latency=latency,
            embeddings=embeddings,
            tokens_in=total_tokens,
        )

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.ON_PREM, "Invalid provider type"
            return True
        except AssertionError as e:
            logging.error(f"On-Prem LLM Provider Validation Failed: {e}")
            return False
