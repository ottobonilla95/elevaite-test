import time
import base64
import logging
import requests
import textwrap
from typing import Any, Dict, Optional, List, Iterable, Callable


from ...utilities.onprem import get_model_endpoint
from ...utilities.tokens import count_tokens
from .core.base import BaseTextGenerationProvider
from .core.interfaces import TextGenerationResponse, ToolCallTrace
from ...tools.web_search import web_search, format_search_results


class OnPremTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, user: str, secret: str):
        if not all([user, secret]):
            raise EnvironmentError(
                "ONPREM_TEXTGEN_ENDPOINT, ONPREM_USER, and ONPREM_SECRET must be set"
            )

        self.user = user
        self.secret = secret

    def generate_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        files: Optional[List[str]] = None,
        max_tool_iterations: int = 4,
    ) -> TextGenerationResponse:
        if files:
            raise NotImplementedError(
                "File search is only supported by the OpenAI provider"
            )
        model_name = model_name or "Llama-3.1-8B-Instruct"
        temperature = temperature if temperature is not None else 0.5
        max_tokens = max_tokens if max_tokens is not None else 100
        sys_msg = sys_msg or ""
        prompt = prompt or ""
        retries = retries if retries is not None else 5
        config = config or {}

        # Handle web_search tool specially - execute it and prepend results to prompt
        web_search_results = None
        if tools:
            has_web_search = any(t.get("type") == "web_search" for t in tools)
            other_tools = [t for t in tools if t.get("type") != "web_search"]

            if has_web_search:
                # For On-Prem, we'll execute web search proactively if the prompt seems to need it
                # The model can't call tools, so we provide context upfront
                logging.info(
                    "Web search tool requested for OnPrem provider - will execute if query detected"
                )
                web_search_results = self._check_and_execute_web_search(prompt)

            if other_tools:
                logging.warning(
                    "Tools (except web_search) are not yet supported by the OnPrem provider. Ignoring tools parameter."
                )

        role: str = config.get("role", "assistant")
        task_prop: str = config.get("task", "")
        output_prop: str = config.get("output", "")

        # Prepend web search results to prompt if available
        effective_prompt = prompt
        if web_search_results:
            effective_prompt = f"**Web Search Results:**\n{web_search_results}\n\n**User Query:**\n{prompt}"

        onprem_prompt = ""

        if "llama" in model_name.lower():
            examples_string = ""
            examples_counter = 1
            while True:
                example_in_prop = config.get(f"example_input {examples_counter}", None)
                expected_out_prop = config.get(
                    f"expected_output {examples_counter}", None
                )

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

            {effective_prompt}

            <|context|>

            <|start_header_id|>{role}<|end_header_id|>
            """
            )

        onprem_generation_args = {
            "text_inputs": onprem_prompt,
            "max_new_tokens": config.get("max_tokens", max_tokens),
            "return_full_text": False,
            "temperature": config.get("temperature", temperature),
            "do_sample": config.get("do_sample", False),
        }

        headers = {"Content-Type": "application/json"}

        auth_value = base64.b64encode(f"{self.user}:{self.secret}".encode()).decode(
            "utf-8"
        )
        headers["Authorization"] = f"Basic {auth_value}"

        payload = {"kwargs": onprem_generation_args}

        for attempt in range(retries):
            try:
                if self.user is None or self.secret is None:
                    raise EnvironmentError("Missing required authentication details.")

                tokens_in = count_tokens([onprem_prompt])
                start_time = time.time()
                response = requests.post(
                    get_model_endpoint(model_name),
                    json=payload,
                    headers=headers,
                    verify=True,
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

    def stream_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        files: Optional[List[str]] = None,
        max_tool_iterations: int = 4,
        on_tool_call: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_tool_result: Optional[Callable[[str, ToolCallTrace], None]] = None,
    ) -> Iterable[Dict[str, Any]]:
        """Stream text generation for OnPrem provider.

        Note: OnPrem provider does not support true streaming or tool calling.
        This method wraps generate_text() and yields the result as a single chunk.
        """
        # OnPrem doesn't support streaming, so we call generate_text and yield the result
        response = self.generate_text(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            sys_msg=sys_msg,
            prompt=prompt,
            retries=retries,
            config=config,
            tools=tools,
            tool_choice=tool_choice,
            messages=messages,
            response_format=response_format,
            files=files,
            max_tool_iterations=max_tool_iterations,
        )

        # Yield the full text as a single delta
        if response.text:
            yield {"type": "delta", "text": response.text}

        # Yield the final response
        yield {"type": "final", "response": response.model_dump()}

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config.get("model"), str), "Model name must be a string"
            assert isinstance(config.get("temperature", 0.01), (float, int)), (
                "Temperature must be a number"
            )
            assert isinstance(config.get("max_tokens", 8000), int), (
                "Max tokens must be an integer"
            )
            assert isinstance(config.get("do_sample", False), bool), (
                "do_sample must be a boolean"
            )
            return True
        except AssertionError as e:
            logging.error(f"On-Prem Provider Validation Failed: {e}")
            return False

    def _check_and_execute_web_search(self, prompt: str) -> Optional[str]:
        """
        Check if the prompt likely needs web search and execute if so.

        Since On-Prem models can't call tools, we proactively search
        when the prompt contains indicators of needing current information.

        Args:
            prompt: The user prompt

        Returns:
            Formatted search results or None
        """
        # Simple heuristics to detect if web search might be needed
        search_indicators = [
            "search for",
            "look up",
            "find information",
            "current",
            "latest",
            "recent",
            "today",
            "what is",
            "who is",
            "where is",
            "when is",
            "news about",
            "updates on",
        ]

        prompt_lower = prompt.lower()
        should_search = any(
            indicator in prompt_lower for indicator in search_indicators
        )

        if not should_search:
            return None

        try:
            # Extract a search query from the prompt (use first 100 chars as query)
            query = prompt[:200].strip()
            results = web_search(query=query, num_results=2)
            return format_search_results(results, include_content=True)
        except Exception as e:
            logging.warning(f"Web search for OnPrem failed: {e}")
            return None

    def execute_web_search(self, query: str, num_results: int = 3) -> str:
        """
        Execute a web search using the fallback implementation.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            Formatted search results as a string
        """
        try:
            results = web_search(query=query, num_results=num_results)
            return format_search_results(results, include_content=True)
        except Exception as e:
            logging.error(f"Web search failed: {e}")
            return f"Web search failed: {e}"
