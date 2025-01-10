import time
import base64
import logging
import requests
import textwrap
from typing import Any, Dict


from .core.base import BaseTextGenerationProvider


class OnPremTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_url: str, user: str, secret: str):
        if not all([api_url, user, secret]):
            raise EnvironmentError(
                "ONPREM_TEXTGEN_ENDPOINT, ONPREM_USER, and ONPREM_SECRET must be set"
            )

        self.api_url = api_url
        self.user = user
        self.secret = secret

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        retries = config.get("retries", 5)
        sys_msg = config.get("sys_msg", "")
        role = config.get("role", "assistant")
        task_prop = config.get("task", "")
        output_prop = config.get("output", "")
        example_in_prop = config.get("example_input", "")
        example_out_prop = config.get("example_output", "")
        onprem_prompt = textwrap.dedent(
            f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        
        {sys_msg}
        
        **Input:** {input}
        
        **Task:** {task_prop}
        
        **Output:** {output_prop}
        
        **Example Input 1:** {example_in_prop}

        Expected Output 1:** {example_out_prop}
        
        <|eot_id|><|start_header_id|>user<|end_header_id|>
        
        <|context|>
        
        {prompt}
        
        <|context|>
        
        <|start_header_id|>{role}<|end_header_id|>
        """
        )

        custom_generation_args = {
            "text_inputs": onprem_prompt,
            "max_new_tokens": config.get("max_tokens", 8000),
            "return_full_text": False,
            "temperature": config.get("temperature", 0.01),
            "do_sample": config.get("do_sample", False),
        }

        headers = {"Content-Type": "application/json"}

        auth_value = base64.b64encode(f"{self.user}:{self.secret}".encode()).decode(
            "utf-8"
        )
        headers["Authorization"] = f"Basic {auth_value}"

        payload = {"kwargs": custom_generation_args}

        for attempt in range(retries):
            try:
                if self.api_url is None or self.user is None or self.secret is None:
                    raise EnvironmentError("Missing required authentication details.")

                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    verify=False,  # FIXME: Disabling SSL verification, for now
                )

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and len(data["result"]) > 0:
                        processed_output = data["result"][0]["generated_text"]
                        return processed_output.strip()
                    else:
                        logging.error(
                            "Failed to find the expected 'result' in the response."
                        )
                        return ""
                else:
                    logging.warning(
                        f"Attempt {attempt + 1}/{retries} failed: {response.text}. Retrying..."
                    )
                    if attempt == retries - 1:
                        raise RuntimeError(
                            f"Text generation failed after {retries} attempts: {response.text}"
                        )
                time.sleep((2**attempt) * 0.5)
            except requests.exceptions.RequestException as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Text generation failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)

        return ""

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates the configuration for On-Prem text generation.
        :param config: Configuration options (e.g., model, temperature, max_tokens).
        :return: True if configuration is valid, False otherwise.
        """
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config.get("model"), str), "Model name must be a string"
            assert isinstance(
                config.get("temperature", 0.01), (float, int)
            ), "Temperature must be a number"
            assert isinstance(
                config.get("max_tokens", 8000), int
            ), "Max tokens must be an integer"
            assert isinstance(
                config.get("do_sample", False), bool
            ), "do_sample must be a boolean"
            return True
        except AssertionError as e:
            logging.error(f"On-Prem Provider Validation Failed: {e}")
            return False
