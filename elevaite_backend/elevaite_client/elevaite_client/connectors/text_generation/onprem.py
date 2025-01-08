import time
import logging
import requests
import textwrap
from typing import Dict, Any
from requests.auth import HTTPBasicAuth


from .core.abstract import BaseTextGenerationProvider


class OnPremTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_url: str, user: str, secret: str):
        if not all([api_url, user, secret]):
            raise EnvironmentError(
                "ONPREM_ENDPOINT, ONPREM_USER, and ONPREM_SECRET must be set"
            )

        self.api_url = api_url
        self.user = user
        self.secret = secret

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        Generates text using the on-prem LLM API.
        :param prompt: The input text prompt.
        :param config: Configuration options (e.g., model, temperature, max_tokens).
        :return: Generated text as a string.
        """
        retries = config.get("retries", 5)
        model = config.get("model", "Llama-3.1-8B-Instruct")

        # TODO: Adjust this
        onprem_prompt = textwrap.dedent(
            f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        
        You are an AI that does this and that
        
        **Input:** The prompt will be within the <|context|> tags<|context|>
        
        **Task:** Extract all entities from the input text and convert them into a dictionary, following these rules:
        
        1. Follow this.
        2. Follow this too.
        3. Follow that.
        
        **Output:** <|dict|>short instruction for the llm<|end_dict|>
        
        **Example Input 1:**
        <|context|>   
        Address 1234
        Date : 01/08/2025
        <|context|>
        Expected Output 1:** 
        <|dict|>{{ 
                'DictKey': 'DictValue',
        }}
        
        <|eot_id|><|start_header_id|>user<|end_header_id|>
        
        <|context|>
        
        {prompt}
        
        <|context|>
        
        <|start_header_id|>assistant<|end_header_id|>
        """
        )

        custom_generation_args = {
            "max_new_tokens": config.get("max_tokens", 8000),
            "return_full_text": False,
            "temperature": config.get("temperature", 0.01),
            "do_sample": config.get("do_sample", False),
        }

        headers = {"Content-Type": "application/json"}

        payload = {
            "inputs": onprem_prompt,
            "parameters": custom_generation_args,
        }

        auth = HTTPBasicAuth(self.user, self.secret)

        for attempt in range(retries):
            try:
                if self.api_url is None or self.user is None or self.secret is None:
                    raise EnvironmentError("Missing required authentication details.")

                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    auth=auth,
                    verify=False,
                )

                if response.status_code == 200:
                    data = response.json()
                    processed_output = data["result"][0]["generated_text"]
                    return processed_output.strip()
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
