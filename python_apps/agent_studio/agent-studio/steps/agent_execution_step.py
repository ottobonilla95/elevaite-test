"""
Agent Execution Step for Deterministic Workflows

This step allows executing agents within deterministic workflows, enabling
integration of AI agent capabilities with structured workflow processing.
"""

import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from steps.base_deterministic_step import (
    BaseDeterministicStep,
    StepConfig,
    StepResult,
    StepStatus,
    StepValidationResult,
)
from services.workflow_execution_context import DeterministicStepType
from fastapi_logger import ElevaiteLogger


class AgentExecutionStepConfig(StepConfig):
    """Configuration for agent execution step"""

    def __init__(self, step_id: str, step_name: str, config: Dict[str, Any]):
        super().__init__(
            step_id=step_id,
            step_name=step_name,
            step_type=DeterministicStepType.DATA_PROCESSING,
            config=config,
        )


class AgentExecutionStep(BaseDeterministicStep):
    """
    Execute an agent within a deterministic workflow.

    This step can:
    - Execute agents by ID or create dynamic agents from configuration
    - Pass workflow data to agents as context
    - Handle agent responses and integrate them back into workflow
    - Support both simple queries and complex agent configurations

    Configuration options:
    - agent_id: ID of existing agent to execute (optional)
    - agent_config: Configuration for dynamic agent creation (optional)
    - query: Query/prompt to send to agent
    - context_mapping: How to map workflow data to agent context
    - response_processing: How to process agent response
    """

    def __init__(self, config: AgentExecutionStepConfig):
        super().__init__(config)
        self.logger = ElevaiteLogger()

    def validate_config(self) -> StepValidationResult:
        """Validate agent execution configuration"""
        result = StepValidationResult()
        config = self.config.config

        # Must have either agent_id or agent_config
        agent_id = config.get("agent_id")
        agent_config = config.get("agent_config")

        if not agent_id and not agent_config:
            result.errors.append("Either 'agent_id' or 'agent_config' must be provided")

        # Must have a query or query template
        query = config.get("query")
        query_template = config.get("query_template")

        if not query and not query_template:
            result.errors.append("Either 'query' or 'query_template' must be provided")

        # Validate agent_config if provided
        if agent_config:
            required_agent_fields = ["agent_name", "model"]
            for field in required_agent_fields:
                if field not in agent_config:
                    result.errors.append(
                        f"agent_config missing required field: {field}"
                    )

        result.is_valid = len(result.errors) == 0
        return result

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute the agent with workflow context"""
        try:
            config = self.config.config

            # Prepare agent execution
            agent_id = config.get("agent_id")
            agent_config = config.get("agent_config")

            # Build query from template or use direct query
            query = self._build_query(config, input_data)

            # Prepare execution context
            execution_context = self._prepare_execution_context(config, input_data)

            self._update_progress(
                current_operation=f"Executing agent: {agent_config.get('agent_name', agent_id) if agent_config else agent_id}",
                total_items=1,
                processed_items=0,
            )

            # Execute agent
            if agent_id:
                result = await self._execute_existing_agent(
                    agent_id, query, execution_context
                )
            else:
                result = await self._execute_dynamic_agent(
                    agent_config, query, execution_context
                )

            # Process response
            processed_result = self._process_agent_response(result, config, input_data)

            self._update_progress(
                processed_items=1, total_items=1, progress_percentage=100
            )

            self.logger.info(f"Agent execution completed successfully")

            return StepResult(status=StepStatus.COMPLETED, data=processed_result)

        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED, error=f"Agent execution error: {str(e)}"
            )

    def _build_query(self, config: Dict[str, Any], input_data: Dict[str, Any]) -> str:
        """Build query from template or use direct query"""
        query = config.get("query")
        query_template = config.get("query_template")

        if query_template:
            # Simple template substitution
            try:
                return query_template.format(**input_data)
            except KeyError as e:
                raise ValueError(f"Query template references missing data: {e}")

        return query or "Please analyze the provided data."

    def _prepare_execution_context(
        self, config: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare execution context for agent"""
        context = {
            "session_id": str(uuid.uuid4()),
            "user_id": "workflow_system",
            "enable_analytics": True,
            "chat_history": [],
            "workflow_context": input_data,
        }

        # Add any additional context from config
        additional_context = config.get("execution_context", {})
        context.update(additional_context)

        return context

    async def _execute_existing_agent(
        self, agent_id: str, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an existing agent by ID"""
        try:
            from db.database import get_db
            from db import crud
            from api.agent_endpoints import _create_agent_instance_from_db

            # Get database session
            db = next(get_db())

            try:
                # Get agent from database
                db_agent = crud.get_agent(db=db, agent_id=uuid.UUID(agent_id))
                if not db_agent:
                    raise ValueError(f"Agent not found: {agent_id}")

                if not db_agent.available_for_deployment:
                    raise ValueError(f"Agent not available for execution: {agent_id}")

                # Create agent instance
                agent_instance = _create_agent_instance_from_db(db, db_agent)

                # Execute agent
                start_time = datetime.now()

                response = agent_instance.execute(
                    query=query,
                    session_id=context.get("session_id"),
                    user_id=context.get("user_id"),
                    chat_history=context.get("chat_history", []),
                    enable_analytics=context.get("enable_analytics", True),
                )

                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()

                return {
                    "status": "completed",
                    "response": response,
                    "agent_id": agent_id,
                    "execution_time": execution_time,
                    "timestamp": end_time.isoformat(),
                }

            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"Error executing existing agent {agent_id}: {e}")
            raise

    async def _execute_dynamic_agent(
        self, agent_config: Dict[str, Any], query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a dynamically created agent"""
        try:
            # Create dynamic agent based on configuration
            agent_instance = self._create_dynamic_agent(agent_config)

            # Execute agent
            start_time = datetime.now()

            response = agent_instance.execute(
                query=query,
                session_id=context.get("session_id"),
                user_id=context.get("user_id"),
                chat_history=context.get("chat_history", []),
                enable_analytics=context.get("enable_analytics", True),
            )

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "status": "completed",
                "response": response,
                "agent_name": agent_config.get("agent_name"),
                "execution_time": execution_time,
                "timestamp": end_time.isoformat(),
                "tools_used": getattr(agent_instance, "tools_used", []),
            }

        except Exception as e:
            self.logger.error(f"Error executing dynamic agent: {e}")
            raise

    def _create_dynamic_agent(self, agent_config: Dict[str, Any]):
        """Create a dynamic agent from configuration"""
        try:
            from agents.command_agent import CommandAgent
            from agents.tools import tool_schemas
            from data_classes import PromptObject

            # Get agent configuration
            agent_name = agent_config.get("agent_name", "Dynamic Agent")
            model = agent_config.get("model", "gpt-4o-mini")
            temperature = agent_config.get("temperature", 0.1)
            max_tokens = agent_config.get("max_tokens", 1000)
            system_prompt_text = agent_config.get(
                "system_prompt", "You are a helpful AI assistant."
            )
            tools = agent_config.get("tools", [])

            # Create PromptObject for system_prompt using the pattern from workflow_agent_builders.py
            from datetime import datetime
            import uuid

            system_prompt = PromptObject(
                appName="DynamicAgent",
                createdTime=datetime.now(),
                prompt=system_prompt_text,
                uniqueLabel=f"{agent_name}_prompt",
                pid=uuid.uuid4(),
                last_deployed=None,
                deployedTime=None,
                isDeployed=False,
                modelProvider="OpenAI",
                modelName=model,
                sha_hash="dynamic_agent_hash",
                tags=[],
                version="1.0",
                variables={},
                hyper_parameters={},
                prompt_label=f"{agent_name} System Prompt",
            )

            # Prepare tool functions
            functions = []
            for tool_name in tools:
                if tool_name in tool_schemas:
                    functions.append(tool_schemas[tool_name])
                else:
                    self.logger.warning(f"Tool not found: {tool_name}")

            # Create agent instance with all required fields
            agent = CommandAgent(
                name=agent_name,
                agent_id=uuid.uuid4(),  # Generate unique agent ID
                system_prompt=system_prompt,
                persona=f"Dynamic agent for {agent_name}",  # Required field
                routing_options={},  # Required field - empty dict for dynamic agents
                failure_strategies=["retry", "fallback"],  # Required field
                model=model,
                temperature=temperature,
                functions=functions,
            )

            return agent

        except Exception as e:
            self.logger.error(f"Error creating dynamic agent: {e}")
            raise

    def _process_agent_response(
        self,
        agent_result: Dict[str, Any],
        config: Dict[str, Any],
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process agent response and integrate with workflow data"""

        # Check if we should return a simplified response
        return_simplified = config.get("return_simplified", False)

        if return_simplified:
            # Return a simplified structure with just the essential data
            result = {
                "response": agent_result.get("response", ""),
                "success": agent_result.get("status") == "completed",
                "execution_time": agent_result.get("execution_time"),
                "agent_name": agent_result.get(
                    "agent_name", agent_result.get("agent_id")
                ),
                "tools_used": agent_result.get("tools_used", []),
                "timestamp": agent_result.get("timestamp"),
            }
        else:
            # Base result with agent execution data (full structure)
            result = {
                "agent_execution": agent_result,
                "success": agent_result.get("status") == "completed",
                # Extract the actual response for easier access
                "response": agent_result.get("response", ""),
                "agent_id": agent_result.get("agent_id"),
                "agent_name": agent_result.get("agent_name"),
            }

        # Add original input data if requested (but not by default to reduce size)
        if config.get("include_input_data", False):
            result["input_data"] = input_data

        # Extract specific fields if configured
        response_mapping = config.get("response_mapping", {})
        if response_mapping:
            for output_key, source_path in response_mapping.items():
                try:
                    # Simple dot notation support
                    value = agent_result
                    for key in source_path.split("."):
                        value = value[key]
                    result[output_key] = value
                except (KeyError, TypeError):
                    self.logger.warning(
                        f"Could not extract {source_path} from agent response"
                    )

        # Add metadata
        result["metadata"] = {
            "step_type": "agent_execution",
            "agent_name": agent_result.get("agent_name", agent_result.get("agent_id")),
            "execution_time": agent_result.get("execution_time"),
            "timestamp": agent_result.get("timestamp"),
            "tools_used": agent_result.get("tools_used", []),
        }

        return result


# Step registration functions
async def create_agent_execution_step(
    step_config: Dict[str, Any], input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step implementation wrapper for AgentExecutionStep"""

    # Check if this is an agent execution step
    config_dict = step_config.get("config", {})
    processing_type = config_dict.get("processing_type")

    if processing_type != "agent_execution":
        # Not an agent execution step, return error
        return {
            "error": f"Unsupported processing_type: {processing_type}",
            "success": False,
        }

    config = AgentExecutionStepConfig(
        step_id=step_config.get("step_id", ""),
        step_name=step_config.get("step_name", ""),
        config=config_dict,
    )

    step = AgentExecutionStep(config)
    result = await step.execute(input_data)
    return result.data or {}


def register_agent_execution_step():
    """Register agent execution step with workflow execution context"""
    try:
        from services.workflow_execution_context import workflow_execution_context

        # Register as agent execution step type directly in the registry
        workflow_execution_context._step_registry["agent_execution"] = (
            create_agent_execution_step_direct
        )

        print("✅ Agent execution step registered successfully")
        print(
            f"✅ Current registered steps: {list(workflow_execution_context._step_registry.keys())}"
        )

    except ImportError as e:
        print(f"⚠️  Could not register agent execution step: {e}")
    except Exception as e:
        print(f"❌ Error registering agent execution step: {e}")


async def create_agent_execution_step_direct(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Direct agent execution step implementation"""
    config = AgentExecutionStepConfig(
        step_id=step_config.get("step_id", ""),
        step_name=step_config.get("step_name", ""),
        config=step_config.get("config", {}),
    )

    step = AgentExecutionStep(config)

    # Use execution_context if available for additional context
    if execution_context:
        # Could potentially use execution_context for session info, etc.
        # For now, just pass through the input_data
        pass

    result = await step.execute(input_data)
    return result.data or {}
