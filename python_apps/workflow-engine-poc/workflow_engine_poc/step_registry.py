"""
Step Registry System

Manages registration and execution of workflow steps.
Supports local functions, RPC endpoints, and API calls.
"""

import uuid
import importlib
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
import logging

from .execution_context import ExecutionContext, StepResult
from workflow_core_sdk.models import StepStatus
from .monitoring import monitoring


logger = logging.getLogger(__name__)


class StepExecutionError(Exception):
    """Exception raised during step execution"""

    pass


class StepRegistry:
    """
    Registry for workflow step functions.

    Supports:
    - Local Python functions
    - RPC endpoints
    - REST API calls
    - Dynamic registration
    """

    def __init__(self):
        self.registered_steps: Dict[str, Dict[str, Any]] = {}
        self.step_functions: Dict[str, Callable] = {}

    async def register_step(self, step_config: Dict[str, Any]) -> str:
        """Register a new step type"""
        step_type = step_config["step_type"]
        step_id = str(uuid.uuid4())

        # Validate step configuration
        required_fields = ["step_type", "name", "function_reference", "execution_type"]
        for field in required_fields:
            if field not in step_config:
                raise ValueError(f"Missing required field: {field}")

        # Store step configuration
        self.registered_steps[step_type] = {
            "step_id": step_id,
            "step_type": step_type,
            "name": step_config["name"],
            "description": step_config.get("description", ""),
            "function_reference": step_config["function_reference"],
            "execution_type": step_config["execution_type"],
            "parameters_schema": step_config.get("parameters_schema", {}),
            "output_schema": step_config.get("output_schema", {}),
            "endpoint_config": step_config.get("endpoint_config", {}),
            "tags": step_config.get("tags", []),
            "registered_at": datetime.now().isoformat(),
        }

        # Load function if it's a local execution type
        if step_config["execution_type"] == "local":
            await self._load_local_function(step_type, step_config["function_reference"])

        logger.info(f"Registered step type: {step_type} ({step_config['execution_type']})")
        return step_id

    async def _load_local_function(self, step_type: str, function_reference: str):
        """Load a local Python function"""
        try:
            # Parse module.function format
            if "." not in function_reference:
                raise ValueError(f"Invalid function reference: {function_reference}")

            module_path, function_name = function_reference.rsplit(".", 1)

            # Import module and get function
            module = importlib.import_module(module_path)
            function = getattr(module, function_name)

            # Store function
            self.step_functions[step_type] = function

        except Exception as e:
            logger.error(f"Failed to load function {function_reference}: {e}")
            raise StepExecutionError(f"Failed to load function: {e}")

    async def execute_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> StepResult:
        """Execute a step based on its type"""

        if step_type not in self.registered_steps:
            raise StepExecutionError(f"Unknown step type: {step_type}")

        step_info = self.registered_steps[step_type]
        execution_type = step_info["execution_type"]

        start_time = datetime.now()
        step_id = step_config.get("step_id", "unknown")

        # Start step tracing
        with monitoring.trace_step_execution(
            step_id=step_id,
            step_type=step_type,
            execution_id=execution_context.execution_id,
        ):
            try:
                # Execute based on execution type
                if execution_type == "local":
                    result = await self._execute_local_step(step_type, step_config, input_data, execution_context)
                elif execution_type == "rpc":
                    result = await self._execute_rpc_step(step_type, step_config, input_data, execution_context)
                elif execution_type == "api":
                    result = await self._execute_api_step(step_type, step_config, input_data, execution_context)
                elif execution_type == "grpc":
                    result = await self._execute_grpc_step(step_type, step_config, input_data, execution_context)
                else:
                    raise Exception(f"Unknown execution type: {execution_type}")

                # Calculate execution time
                end_time = datetime.now()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

                # If the step returned a StepResult, propagate it (supports WAITING/FAILED/etc.)
                if isinstance(result, StepResult):
                    if result.execution_time_ms is None:
                        result.execution_time_ms = execution_time_ms
                    return result

                # If the step returned a dict indicating WAITING, map to a WAITING StepResult
                if isinstance(result, dict) and str(result.get("status", "")).lower() == "waiting":
                    return StepResult(
                        step_id=step_id,
                        status=StepStatus.WAITING,
                        output_data=result,
                        execution_time_ms=execution_time_ms,
                    )

                # Otherwise, wrap raw output as a completed step
                return StepResult(
                    step_id=step_id,
                    status=StepStatus.COMPLETED,
                    output_data=result,
                    execution_time_ms=execution_time_ms,
                )

            except Exception as e:
                # Calculate execution time even for failed steps
                end_time = datetime.now()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

                # Return failed step result
                return StepResult(
                    step_id=step_id,
                    status=StepStatus.FAILED,
                    error_message=str(e),
                    execution_time_ms=execution_time_ms,
                )

    async def _execute_local_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute a local Python function"""

        if step_type not in self.step_functions:
            raise StepExecutionError(f"Function not loaded for step type: {step_type}")

        function = self.step_functions[step_type]

        # Prepare function arguments
        kwargs = {
            "step_config": step_config,
            "input_data": input_data,
            "execution_context": execution_context,
        }

        # Execute function (handle both sync and async)
        if asyncio.iscoroutinefunction(function):
            result = await function(**kwargs)
        else:
            result = function(**kwargs)

        return result

    async def _execute_rpc_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute an RPC step"""
        step_info = self.registered_steps[step_type]
        endpoint_config = step_info["endpoint_config"]

        # Prepare RPC call
        rpc_url = endpoint_config.get("url")
        if not rpc_url:
            raise StepExecutionError("RPC URL not configured")

        payload = {
            "step_config": step_config,
            "input_data": input_data,
            "execution_context": {
                "execution_id": execution_context.execution_id,
                "workflow_id": execution_context.workflow_id,
                "user_context": {
                    "user_id": execution_context.user_context.user_id,
                    "session_id": execution_context.user_context.session_id,
                },
            },
        }

        # Make RPC call
        timeout = endpoint_config.get("timeout", 30)
        async with aiohttp.ClientSession() as session:
            async with session.post(rpc_url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status != 200:
                    raise StepExecutionError(f"RPC call failed: {response.status}")

                result = await response.json()
                return result

    async def _execute_api_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute an API step"""
        step_info = self.registered_steps[step_type]
        endpoint_config = step_info["endpoint_config"]

        # Prepare API call
        api_url = endpoint_config.get("url")
        method = endpoint_config.get("method", "POST").upper()
        headers = endpoint_config.get("headers", {})

        if not api_url:
            raise StepExecutionError("API URL not configured")

        # Prepare request data
        request_data = {"step_config": step_config, "input_data": input_data}

        # Make API call
        timeout = endpoint_config.get("timeout", 30)
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                api_url,
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status not in [200, 201]:
                    raise StepExecutionError(f"API call failed: {response.status}")
                result = await response.json()
                return result

    async def _execute_grpc_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute a gRPC step via a user-provided invoker.

        Design:
        - Keep this registry light by delegating heavy gRPC client code to an external package/app.
        - endpoint_config.invoker should be a dotted path to a callable that performs the gRPC call.
          Example: "elevaite_ingestion.client.vectorize_invoker"
        - The callable can be sync or async and must accept kwargs: step_config, input_data, execution_context, endpoint_config.
        - It should return a JSON-serializable dict or a StepResult.
        """
        step_info = self.registered_steps[step_type]
        endpoint_config = step_info.get("endpoint_config", {}) or {}
        invoker_ref = endpoint_config.get("invoker")
        if not invoker_ref:
            raise StepExecutionError(
                "gRPC invoker not configured; set endpoint_config.invoker to '<module>:<callable>' or '<module>.<callable>'"
            )

        # Support both module:function and module.function formats
        if ":" in invoker_ref:
            module_path, func_name = invoker_ref.split(":", 1)
        else:
            module_path, func_name = invoker_ref.rsplit(".", 1)

        try:
            mod = importlib.import_module(module_path)
            invoker = getattr(mod, func_name)
        except Exception as e:
            raise StepExecutionError(f"Failed to import gRPC invoker '{invoker_ref}': {e}")

        kwargs = {
            "step_config": step_config,
            "input_data": input_data,
            "execution_context": execution_context,
            "endpoint_config": endpoint_config,
        }

        try:
            if asyncio.iscoroutinefunction(invoker):
                return await invoker(**kwargs)
            else:
                return invoker(**kwargs)
        except Exception as e:
            # Surface underlying gRPC/client errors as step failures
            raise StepExecutionError(f"gRPC invoker execution failed: {e}")

    async def get_registered_steps(self) -> List[Dict[str, Any]]:
        """Get list of all registered steps"""
        return list(self.registered_steps.values())

    async def get_step_info(self, step_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific step type"""
        return self.registered_steps.get(step_type)

    async def unregister_step(self, step_type: str) -> bool:
        """Unregister a step type"""
        if step_type in self.registered_steps:
            del self.registered_steps[step_type]
            if step_type in self.step_functions:
                del self.step_functions[step_type]
            logger.info(f"Unregistered step type: {step_type}")
            return True
        return False

    async def register_builtin_steps(self):
        """Register built-in step types"""

        # Register trigger step (must be first in workflow)
        await self.register_step(
            {
                "step_type": "trigger",
                "name": "Trigger",
                "description": "Validates and normalizes workflow input (chat/webhook/file)",
                "function_reference": "workflow_engine_poc.steps.trigger_steps.trigger_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["chat", "webhook", "file"]},
                        "need_history": {"type": "boolean"},
                        "allowed_modalities": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["text", "image", "audio"]},
                        },
                        "max_files": {"type": "integer", "minimum": 0},
                        "per_file_size_mb": {"type": "integer", "minimum": 1},
                        "total_size_mb": {"type": "integer", "minimum": 1},
                        "allowed_mime_types": {"type": "array", "items": {"type": "string"}},
                        "schedule": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean", "default": False},
                                "mode": {"type": "string", "enum": ["interval", "cron"], "default": "interval"},
                                "interval_seconds": {"type": "integer", "minimum": 5},
                                "cron": {"type": "string"},
                                "backend": {"type": "string", "enum": ["dbos", "local"], "default": "dbos"},
                                "jitter_seconds": {"type": "integer", "minimum": 0},
                                "timezone": {"type": "string"},
                            },
                        },
                    },
                },
            }
        )

        # Human approval step (pause/resume)
        await self.register_step(
            {
                "step_type": "human_approval",
                "name": "Human Approval",
                "description": "Pauses execution and waits for human approval",
                "function_reference": "workflow_engine_poc.steps.human_steps.human_approval_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "timeout_seconds": {"type": "integer", "minimum": 1},
                        "approver_role": {"type": "string"},
                        "require_comment": {"type": "boolean"},
                    },
                    "required": ["prompt"],
                },
            }
        )

        # Register basic data processing steps
        await self.register_step(
            {
                "step_type": "data_input",
                "name": "Data Input",
                "description": "Provides static or dynamic input data",
                "function_reference": "workflow_engine_poc.steps.data_steps.data_input_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "input_type": {"type": "string", "enum": ["static", "dynamic"]},
                        "data": {"type": "object"},
                    },
                },
            }
        )

        await self.register_step(
            {
                "step_type": "data_processing",
                "name": "Data Processing",
                "description": "Processes input data with various transformations",
                "function_reference": "workflow_engine_poc.steps.data_steps.data_processing_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "processing_type": {"type": "string"},
                        "options": {"type": "object"},
                    },
                },
            }
        )

        await self.register_step(
            {
                "step_type": "data_merge",
                "name": "Data Merge",
                "description": "Merges data from multiple sources",
                "function_reference": "workflow_engine_poc.steps.data_steps.data_merge_step",
                "execution_type": "local",
            }
        )

        # Register agent execution step
        await self.register_step(
            {
                "step_type": "agent_execution",
                "name": "Agent Execution",
                "description": "Executes AI agents with various configurations",
                "function_reference": "workflow_engine_poc.steps.ai_steps.agent_execution_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string"},
                        "system_prompt": {"type": "string"},
                        "query": {"type": "string"},
                        "tools": {"type": "array"},
                        "force_real_llm": {"type": "boolean"},
                    },
                },
            }
        )

        # Register file processing steps for RAG workflows
        await self.register_step(
            {
                "step_type": "file_reader",
                "name": "File Reader",
                "description": "Reads and extracts content from various document formats (PDF, DOCX, XLSX, TXT)",
                "function_reference": "workflow_engine_poc.steps.file_steps.file_reader_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "pdf_method": {
                            "type": "string",
                            "enum": ["pypdf2", "pdfplumber"],
                        },
                        "extract_images": {"type": "boolean"},
                        "extract_tables": {"type": "boolean"},
                    },
                },
            }
        )

        await self.register_step(
            {
                "step_type": "text_chunking",
                "name": "Text Chunking",
                "description": "Divides text into manageable, semantically meaningful chunks",
                "function_reference": "workflow_engine_poc.steps.file_steps.text_chunking_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "enum": ["sliding_window", "semantic"],
                        },
                        "chunk_size": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 5000,
                        },
                        "overlap": {"type": "integer", "minimum": 0, "maximum": 1000},
                    },
                },
            }
        )

        await self.register_step(
            {
                "step_type": "embedding_generation",
                "name": "Embedding Generation",
                "description": "Generates vector embeddings for text chunks using various providers",
                "function_reference": "workflow_engine_poc.steps.file_steps.embedding_generation_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "provider": {
                            "type": "string",
                            "enum": ["openai", "sentence_transformers"],
                        },
                        "model": {"type": "string"},
                        "batch_size": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                },
            }
        )

        await self.register_step(
            {
                "step_type": "vector_storage",
                "name": "Vector Storage",
                "description": "Stores vector embeddings in vector databases for retrieval",
                "function_reference": "workflow_engine_poc.steps.file_steps.vector_storage_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "storage_type": {
                            "type": "string",
                            "enum": ["qdrant", "in_memory"],
                        },
                        "collection_name": {"type": "string"},
                        "qdrant_host": {"type": "string"},
                        "qdrant_port": {"type": "integer"},
                    },
                },
            }
        )

        await self.register_step(
            {
                "step_type": "vector_search",
                "name": "Vector Search",
                "description": "Queries a vector database (e.g., Qdrant) and returns top matching chunks",
                "function_reference": "workflow_engine_poc.steps.file_steps.vector_search_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "db_type": {"type": "string", "enum": ["qdrant"]},
                        "collection_name": {"type": "string"},
                        "qdrant_host": {"type": "string"},
                        "qdrant_port": {"type": "integer"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 100},
                        "provider": {"type": "string"},
                        "model": {"type": "string"},
                        "query": {"type": "string"},
                    },
                },
            }
        )

        # Register subflow step for nested workflow execution
        await self.register_step(
            {
                "step_type": "subflow",
                "name": "Subflow Execution",
                "description": "Executes another workflow as a nested component, enabling composition of complex workflows from smaller reusable components",
                "function_reference": "workflow_engine_poc.steps.flow_steps.subflow_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "ID of the workflow to execute as a subflow",
                        },
                        "input_mapping": {
                            "type": "object",
                            "description": "How to map current input data to subflow input (dot notation supported)",
                            "additionalProperties": {"type": "string"},
                        },
                        "output_mapping": {
                            "type": "object",
                            "description": "How to map subflow output back to current workflow (dot notation supported)",
                            "additionalProperties": {"type": "string"},
                        },
                        "inherit_context": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to inherit user context from parent workflow",
                        },
                    },
                    "required": ["workflow_id"],
                },
            }
        )

        # Register tool execution step (standalone tool as a step)
        await self.register_step(
            {
                "step_type": "tool_execution",
                "name": "Tool Execution",
                "description": "Invokes a tool (local or DB-registered) as a standalone step",
                "function_reference": "workflow_engine_poc.steps.tool_steps.tool_execution_step",
                "execution_type": "local",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {"type": "string"},
                        "tool_id": {"type": "string"},
                        "param_mapping": {"type": "object", "additionalProperties": {"type": "string"}},
                        "static_params": {"type": "object"},
                    },
                },
            }
        )

        logger.info("Built-in steps registered successfully")
