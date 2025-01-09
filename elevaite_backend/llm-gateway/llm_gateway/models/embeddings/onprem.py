import base64
import logging
import time
from typing import List

import requests
from .core.abstract import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingType


class OnPremEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_url: str, user: str, secret: str):
        if not all([api_url, user, secret]):
            raise EnvironmentError(
                "ONPREM_EMBED_ENDPOINT, ONPREM_USER, and ONPREM_SECRET must be set"
            )
        self.api_url = api_url
        self.user = user
        self.secret = secret

    def embed_documents(
        self, texts: List[str], embedding_model: str, max_retries: int = 3
    ) -> List[List[float]]:
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

        for attempt in range(max_retries):
            try:
                logging.info(f"Embedding texts using model: {embedding_model}")
                logging.debug(f"Request Payload: {payload}")

                response = requests.post(
                    self.api_url,
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

                    logging.debug(f"API Response Result: {result}")

                    if isinstance(result, list) and result:
                        embeddings = result
                        logging.debug(f"Extracted Embeddings: {embeddings}")

                        if all(len(vec) > 0 for vec in embeddings):
                            return embeddings
                        else:
                            raise ValueError("Invalid or empty embeddings received.")
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

        raise RuntimeError("Embedding failed after all retry attempts.")

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.ON_PREM, "Invalid provider type"
            assert self.api_url is not None, "API URL required"
            return True
        except AssertionError as e:
            logging.error(f"On-Prem LLM Provider Validation Failed: {e}")
            return False
