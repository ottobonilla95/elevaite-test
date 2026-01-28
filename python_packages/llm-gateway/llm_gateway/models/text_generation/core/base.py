from abc import ABC, abstractmethod
import json
import logging
import time
from typing import Dict, Any, Optional, List, Iterable, Callable, Tuple

from .interfaces import TextGenerationResponse, ToolCall, ToolCallTrace

logger = logging.getLogger(__name__)

# Type alias for tool executor function
ToolExecutor = Callable[..., Any]


class BaseTextGenerationProvider(ABC):
    """Base class for text generation providers with built-in tool execution support.

    Tool Structure (with executor):
    {
        "type": "function",
        "function": {"name": "...", "description": "...", "parameters": {...}},
        "executor": Callable[..., Any],  # Optional: function to execute the tool
    }

    When tools have executors, the provider runs the full tool loop internally,
    calling the LLM, executing tools, and continuing until a final response.
    """

    def _extract_executors(
        self, tools: Optional[List[Dict[str, Any]]]
    ) -> Tuple[Dict[str, ToolExecutor], List[Dict[str, Any]]]:
        """Extract executors from tools, return (executors_map, clean_schemas).

        Args:
            tools: List of tool definitions, optionally with 'executor' key

        Returns:
            Tuple of (executors_map, clean_schemas) where:
            - executors_map: Dict mapping tool name to executor function
            - clean_schemas: Tools with 'executor' key removed (safe for API)
        """
        if not tools:
            return {}, []

        executors: Dict[str, ToolExecutor] = {}
        clean_schemas: List[Dict[str, Any]] = []

        for tool in tools:
            tool_copy = tool.copy()
            executor = tool_copy.pop("executor", None)

            # Get tool name
            tool_type = tool_copy.get("type")
            if tool_type == "function" and "function" in tool_copy:
                name = tool_copy["function"].get("name")
            elif "name" in tool_copy:
                name = tool_copy["name"]
            else:
                name = None

            if executor and name:
                executors[name] = executor

            # Handle built-in code_execution tool type
            # This gets converted to execute_python by providers, so we add the executor here
            if tool_type == "code_execution" and "execute_python" not in executors:
                try:
                    from llm_gateway.tools.code_execution import execute_python

                    executors["execute_python"] = execute_python
                    logger.debug(
                        "Added execute_python executor for code_execution tool"
                    )
                except ImportError:
                    logger.warning(
                        "code_execution tool requested but executor not available"
                    )

            clean_schemas.append(tool_copy)

        return executors, clean_schemas

    def _execute_tool(
        self,
        tool_call: ToolCall,
        executors: Dict[str, ToolExecutor],
    ) -> ToolCallTrace:
        """Execute a tool and return the trace.

        Args:
            tool_call: The tool call from the LLM
            executors: Map of tool name to executor function

        Returns:
            ToolCallTrace with execution result
        """
        start_time = time.time()
        name = tool_call.name
        args = tool_call.arguments

        if name not in executors:
            return ToolCallTrace(
                tool_name=name,
                arguments=args,
                result=None,
                success=False,
                error=f"No executor found for tool: {name}",
                tool_call_id=tool_call.id,
            )

        try:
            executor = executors[name]
            result = executor(**args)
            duration_ms = int((time.time() - start_time) * 1000)

            return ToolCallTrace(
                tool_name=name,
                arguments=args,
                result=result,
                success=True,
                duration_ms=duration_ms,
                tool_call_id=tool_call.id,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Tool execution failed for {name}: {e}")
            return ToolCallTrace(
                tool_name=name,
                arguments=args,
                result=None,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                tool_call_id=tool_call.id,
            )

    def _format_tool_result_as_message(
        self, tool_call: ToolCall, trace: ToolCallTrace
    ) -> Dict[str, Any]:
        """Format tool result as a message for the conversation.

        Args:
            tool_call: The original tool call
            trace: The execution trace with result

        Returns:
            Dict in OpenAI tool message format
        """
        if trace.success:
            result = trace.result
            if isinstance(result, dict):
                content = result.get("response") or json.dumps(result)
            elif isinstance(result, str):
                content = result
            else:
                content = json.dumps(result) if result is not None else ""
        else:
            content = f"Error: {trace.error}"

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": content,
        }

    def _format_assistant_message_with_tool_calls(
        self, response: TextGenerationResponse
    ) -> Dict[str, Any]:
        """Format assistant response with tool calls as a message.

        Args:
            response: The LLM response containing tool calls

        Returns:
            Dict in OpenAI assistant message format with tool_calls
        """
        tool_calls_list = []
        for tc in response.tool_calls or []:
            args_str = (
                json.dumps(tc.arguments)
                if isinstance(tc.arguments, dict)
                else str(tc.arguments)
            )
            tool_calls_list.append(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": args_str,
                    },
                }
            )

        msg: Dict[str, Any] = {"role": "assistant", "tool_calls": tool_calls_list}
        if response.text:
            msg["content"] = response.text
        return msg

    @abstractmethod
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
        """
        Abstract method to generate text based on a given prompt and configuration.

        :param model_name: The name of the model to use for text generation. Defaults to a set selected appropriate model.
        :param temperature: Controls the randomness of the output. A value of 1.0 means standard sampling; lower values make output deterministic. Defaults to 0.5.
        :param max_tokens: The maximum number of tokens in the generated output. Defaults to 100.
        :param sys_msg: A system-level message or instruction to guide text generation. Defaults to blank.
        :param prompt: The user-provided input text prompt. Defaults to blank.
        :param retries: The number of times to retry text generation in case of failure. Defaults to 5.
        :param config: Additional configuration options as a dictionary, e.g., {'role': assistant }. Defaults to {}.
        :param tools: List of tool/function definitions available to the model. Tools may include an 'executor' key
                      with a callable that will be invoked when the LLM calls the tool. Defaults to None.
        :param tool_choice: How the model should choose tools ('auto', 'none', or specific tool name). Defaults to None.
        :param files: List of file paths to upload for file search. Only supported by OpenAI provider. Defaults to None.
        :param max_tool_iterations: Maximum number of tool call iterations before returning. Defaults to 4.
        :return: A `TextGenerationResponse` containing:
                 - 'text': The generated text as a string.
                 - 'tokens_in': Number of input tokens (total across all iterations).
                 - 'tokens_out': Number of output tokens (total across all iterations).
                 - 'latency': The time taken for the response in seconds.
                 - 'tool_calls': List of pending tool calls (only if stopped due to max iterations).
                 - 'tool_calls_trace': History of all tool executions during the loop.
                 - 'finish_reason': Reason the model stopped generating ('stop', 'tool_calls', etc.).
        """
        pass

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
        """Optional streaming interface. Default raises NotImplementedError.

        Yields dict events: {"type": "delta", "text": str} ... and a final
        {"type": "final", "response": TextGenerationResponse.model_dump()}.

        When tools with executors are provided, the provider handles the full tool loop,
        yielding events for tool calls and results via callbacks.

        :param files: List of file paths to upload for file search. Only supported by OpenAI provider. Defaults to None.
        :param max_tool_iterations: Maximum number of tool call iterations before returning. Defaults to 4.
        :param on_tool_call: Optional callback invoked when a tool is about to be called. Args: (tool_name, arguments).
        :param on_tool_result: Optional callback invoked after a tool execution. Args: (tool_name, trace).
        """
        raise NotImplementedError("Streaming not implemented for this provider")

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate provider-specific configuration.
        :param config: Configuration options like model name, temperature, etc.
        :return: True if configuration is valid, False otherwise.
        """
        pass
