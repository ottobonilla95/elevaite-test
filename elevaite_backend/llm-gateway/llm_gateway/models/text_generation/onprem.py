import time
import base64
import logging
import requests
import textwrap
from typing import Any, Dict


from ...utilities.tokens import count_tokens
from .core.base import BaseTextGenerationProvider
from .core.interfaces import TextGenerationResponse


class OnPremTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_url: str, user: str, secret: str):
        if not all([api_url, user, secret]):
            raise EnvironmentError(
                "ONPREM_TEXTGEN_ENDPOINT, ONPREM_USER, and ONPREM_SECRET must be set"
            )

        self.api_url = api_url
        self.user = user
        self.secret = secret

    def generate_text(
        self, prompt: str, config: Dict[str, Any]
    ) -> TextGenerationResponse:
        retries = config.get("retries", 5)
        sys_msg = config.get("sys_msg", "")
        role = config.get("role", "assistant")
        task_prop = config.get("task", "")
        output_prop = config.get("output", "")
        examples_string = ""
        examples_counter = 1
        while True:
            example_in_prop = config.get(f"example_input {examples_counter}", None)
            expected_out_prop = config.get(f"expected_output {examples_counter}", None)

            if example_in_prop is None or expected_out_prop is None:
                break

            examples_string += f"""
        **Example Input {examples_counter}:** {example_in_prop}

        **Expected Output {examples_counter}:** {expected_out_prop}

        """
            examples_counter += 1
        onprem_prompt = textwrap.dedent(
            f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        
        {sys_msg}
        
        **Input:** {input}
        
        **Task:** {task_prop}
        
        **Output:** {output_prop}
        
        {examples_string}
        
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

                tokens_in = count_tokens([onprem_prompt])
                start_time = time.time()
                response = requests.post(
                    self.api_url, json=payload, headers=headers, verify=True
                )
                latency = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and len(data["result"]) > 0:
                        processed_output = data["result"][0]["generated_text"]
                        if processed_output is not None:
                            processed_output = processed_output.strip()
                        tokens_out = count_tokens([processed_output])
                        return TextGenerationResponse(
                            text=processed_output,
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            latency=latency,
                        )
                    else:
                        logging.error(
                            "Failed to find the expected 'result' in the response."
                        )
                        return TextGenerationResponse(
                            text="",
                            tokens_in=tokens_in,
                            tokens_out=-1,
                            latency=latency,
                        )
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

        raise Exception

    def validate_config(self, config: Dict[str, Any]) -> bool:
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
