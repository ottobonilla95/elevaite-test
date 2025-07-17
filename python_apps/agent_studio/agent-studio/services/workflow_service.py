import uuid
import asyncio
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime

from db import crud, schemas, models
from agents.command_agent import CommandAgent
from agents import agent_schemas
from prompts import command_agent_system_prompt


class WorkflowService:
    """Service layer for workflow management"""

    def __init__(self):
        self.active_deployments: Dict[str, Dict[str, Any]] = {}

    def create_modern_workflow(
        self,
        db: Session,
        name: str,
        description: str,
        agents_data: List[Dict[str, Any]],
        connections_data: List[Dict[str, Any]],
        created_by: Optional[str] = None,
    ) -> models.Workflow:
        """
        Create a modern workflow from structured frontend data

        Args:
            db: Database session
            name: Workflow name
            description: Workflow description
            agents_data: List of agent objects with agent_id and position
                Format: [{"agent_id": "uuid", "position": {"x": 100, "y": 50}}, ...]
            connections_data: List of connection objects with source/target agent IDs
                Format: [{"source_agent_id": "uuid1", "target_agent_id": "uuid2", "connection_type": "default"}, ...]
            created_by: User who created the workflow

        Returns:
            Created workflow model
        """
        # Build workflow configuration
        workflow_config = {
            "agents": agents_data,
            "connections": connections_data,
            "metadata": {
                "created_from": "modern_frontend",
                "agent_count": len(agents_data),
                "connection_count": len(connections_data),
            },
        }

        # Create workflow
        workflow_data = schemas.WorkflowCreate(
            name=name,
            description=description,
            configuration=workflow_config,
            created_by=created_by,
        )

        workflow = crud.create_workflow(db, workflow_data)

        # Add agents to workflow
        for agent_data in agents_data:
            try:
                # Modern format: {"agent_id": "uuid", "position": {"x": 100, "y": 50}}
                agent_id = agent_data.get("agent_id")
                position = agent_data.get("position", {})

                if not agent_id:
                    print(f"Warning: Missing agent_id in agent_data: {agent_data}")
                    continue

                # Validate agent exists
                db_agent = crud.get_agent(db, uuid.UUID(agent_id))
                if not db_agent:
                    print(f"Warning: Agent with ID '{agent_id}' not found")
                    continue

                workflow_agent_data = schemas.WorkflowAgentCreate(
                    workflow_id=workflow.workflow_id,
                    agent_id=db_agent.agent_id,
                    node_id=f"node_{agent_id}",
                    position_x=position.get("x"),
                    position_y=position.get("y"),
                    agent_config={"original_data": agent_data},
                )
                crud.create_workflow_agent(db, workflow_agent_data)

            except (ValueError, TypeError) as e:
                print(f"Error processing agent_data {agent_data}: {e}")
                continue

        # Add connections to workflow
        for connection_data in connections_data:
            try:
                # Modern format: {"source_agent_id": "uuid1", "target_agent_id": "uuid2", "connection_type": "default"}
                source_agent_id = connection_data.get("source_agent_id")
                target_agent_id = connection_data.get("target_agent_id")
                connection_type = connection_data.get("connection_type", "default")

                if not source_agent_id or not target_agent_id:
                    print(
                        f"Warning: Missing agent IDs in connection_data: {connection_data}"
                    )
                    continue

                # Validate agents exist
                source_agent = crud.get_agent(db, uuid.UUID(source_agent_id))
                target_agent = crud.get_agent(db, uuid.UUID(target_agent_id))

                if not source_agent:
                    print(
                        f"Warning: Source agent with ID '{source_agent_id}' not found"
                    )
                    continue

                if not target_agent:
                    print(
                        f"Warning: Target agent with ID '{target_agent_id}' not found"
                    )
                    continue

                connection_create_data = schemas.WorkflowConnectionCreate(
                    workflow_id=workflow.workflow_id,
                    source_agent_id=source_agent.agent_id,
                    target_agent_id=target_agent.agent_id,
                    connection_type=connection_type,
                )
                crud.create_workflow_connection(db, connection_create_data)

            except (ValueError, TypeError) as e:
                print(f"Error processing connection_data {connection_data}: {e}")
                continue

        return workflow

    def deploy_workflow(
        self,
        db: Session,
        workflow_id: uuid.UUID,
        deployment_name: str,
        environment: str = "production",
        deployed_by: Optional[str] = None,
    ) -> models.WorkflowDeployment:
        """
        Deploy a workflow and create a CommandAgent instance

        Args:
            db: Database session
            workflow_id: ID of workflow to deploy
            deployment_name: Name for this deployment
            environment: Deployment environment
            deployed_by: User who deployed the workflow

        Returns:
            Created deployment model
        """
        # Get workflow
        workflow = crud.get_workflow(db, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Create deployment record
        deployment_data = schemas.WorkflowDeploymentCreate(
            workflow_id=workflow_id,
            environment=environment,
            deployment_name=deployment_name,
            deployed_by=deployed_by,
        )

        deployment = crud.create_workflow_deployment(db, deployment_data)

        # Determine deployment strategy based on workflow configuration
        deployment_info = self._create_workflow_deployment(db, workflow, deployment)

        # Store in active deployments
        self.active_deployments[deployment_name] = deployment_info

        return deployment

    def execute_workflow(
        self,
        db: Session,
        deployment_name: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a deployed workflow

        Args:
            db: Database session
            deployment_name: Name of deployment to execute
            query: Query to execute
            chat_history: Optional chat history

        Returns:
            Execution result
        """
        if deployment_name not in self.active_deployments:
            raise ValueError(
                f"No active deployment found with name '{deployment_name}'"
            )

        deployment_info = self.active_deployments[deployment_name]
        deployment = deployment_info["deployment"]

        try:
            # Execute based on deployment type
            if deployment_info.get("is_single_agent", False):
                # Single-agent execution
                agent = deployment_info["agent"]
                if hasattr(agent, "execute"):
                    result = agent.execute(query, chat_history)
                else:
                    raise ValueError(
                        f"Agent {deployment_info['agent_type']} does not have execute method"
                    )
            else:
                # Multi-agent execution via CommandAgent
                command_agent = deployment_info["command_agent"]
                if chat_history:
                    result = command_agent.execute_stream(query, chat_history)
                else:
                    result = command_agent.execute(query=query)

            # Update deployment statistics
            deployment_update = schemas.WorkflowDeploymentUpdate()
            crud.update_workflow_deployment(
                db, deployment.deployment_id, deployment_update
            )

            return {
                "status": "success",
                "response": result,
                "deployment_name": deployment_name,
                "workflow_id": deployment.workflow_id,
            }

        except Exception as e:
            # Update error statistics
            deployment_update = schemas.WorkflowDeploymentUpdate(last_error=str(e))
            crud.update_workflow_deployment(
                db, deployment.deployment_id, deployment_update
            )
            raise

    async def execute_workflow_async(
        self,
        db: Session,
        deployment_name: str,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute a deployed workflow asynchronously with streaming responses

        Args:
            db: Database session
            deployment_name: Name of deployment to execute
            query: Query to execute
            chat_history: Optional chat history

        Yields:
            Streaming response chunks
        """
        if deployment_name not in self.active_deployments:
            yield json.dumps(
                {"error": f"No active deployment found with name '{deployment_name}'"}
            )
            return

        deployment_info = self.active_deployments[deployment_name]
        deployment = deployment_info["deployment"]

        try:
            # Send initial status
            yield (
                json.dumps(
                    {
                        "status": "started",
                        "deployment_name": deployment_name,
                        "workflow_id": str(deployment.workflow_id),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                + "\n"
            )

            # Execute based on deployment type
            if deployment_info.get("is_single_agent", False):
                # Single-agent async execution
                agent = deployment_info["agent"]
                if hasattr(agent, "execute_async"):
                    # Use async streaming execution
                    async for chunk in agent.execute_async(query, chat_history):
                        if chunk:
                            yield json.dumps(
                                {
                                    "type": "content",
                                    "data": chunk,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            ) + "\n"
                            await asyncio.sleep(0.01)
                elif hasattr(agent, "execute"):
                    # Fall back to sync execution
                    result = agent.execute(query, chat_history)
                    yield json.dumps(
                        {
                            "type": "content",
                            "data": result,
                            "timestamp": datetime.now().isoformat(),
                        }
                    ) + "\n"
                else:
                    raise ValueError(
                        f"Agent {deployment_info['agent_type']} does not have execute method"
                    )
            else:
                # Multi-agent execution via CommandAgent
                command_agent = deployment_info["command_agent"]
                if chat_history:
                    # Use streaming execution with chat history
                    for chunk in command_agent.execute_stream(query, chat_history):
                        if chunk:
                            # Wrap each chunk in a structured format
                            yield json.dumps(
                                {
                                    "type": "content",
                                    "data": chunk,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            ) + "\n"
                            # Small delay to prevent overwhelming the client
                            await asyncio.sleep(0.01)
                else:
                    # For non-streaming execution, we'll simulate streaming by chunking the response
                    result = command_agent.execute(query=query)

                    # Send the result as a single chunk
                    yield json.dumps(
                        {
                            "type": "content",
                            "data": result,
                            "timestamp": datetime.now().isoformat(),
                        }
                    ) + "\n"

            # Send completion status
            yield (
                json.dumps(
                    {
                        "status": "completed",
                        "deployment_name": deployment_name,
                        "workflow_id": str(deployment.workflow_id),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                + "\n"
            )

            # Update deployment statistics
            deployment_update = schemas.WorkflowDeploymentUpdate()
            crud.update_workflow_deployment(
                db, deployment.deployment_id, deployment_update
            )

        except Exception as e:
            # Send error status
            yield (
                json.dumps(
                    {
                        "status": "error",
                        "error": str(e),
                        "deployment_name": deployment_name,
                        "workflow_id": str(deployment.workflow_id),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                + "\n"
            )

            # Update error statistics
            deployment_update = schemas.WorkflowDeploymentUpdate(last_error=str(e))
            crud.update_workflow_deployment(
                db, deployment.deployment_id, deployment_update
            )

    def stop_deployment(self, db: Session, deployment_name: str) -> bool:
        """
        Stop an active deployment

        Args:
            db: Database session
            deployment_name: Name of deployment to stop

        Returns:
            True if stopped successfully
        """
        if deployment_name not in self.active_deployments:
            return False

        deployment_info = self.active_deployments[deployment_name]
        deployment = deployment_info["deployment"]

        # Update deployment status
        deployment_update = schemas.WorkflowDeploymentUpdate(status="inactive")
        crud.update_workflow_deployment(db, deployment.deployment_id, deployment_update)

        # Remove from active deployments
        del self.active_deployments[deployment_name]

        return True

    def get_active_deployments(self) -> Dict[str, Dict[str, Any]]:
        """Get all active deployments"""
        return self.active_deployments

    def _build_command_agent_from_workflow(
        self, db: Session, workflow: models.Workflow
    ) -> CommandAgent:
        """
        Build a CommandAgent from a workflow configuration

        Args:
            db: Database session
            workflow: Workflow model

        Returns:
            Configured CommandAgent
        """
        # Get workflow connections
        workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)

        # Build functions list for CommandAgent using database-stored functions
        functions = []
        for connection in workflow_connections:
            source_agent = crud.get_agent(db, connection.source_agent_id)
            target_agent = crud.get_agent_with_functions(db, connection.target_agent_id)

            if source_agent and source_agent.name == "CommandAgent":
                if target_agent:
                    functions.extend(target_agent.functions)
                    print(
                        f"Added {len(target_agent.functions)} functions from {target_agent.name}"
                    )
                else:
                    target_agent_fallback = crud.get_agent(
                        db, connection.target_agent_id
                    )
                    if (
                        target_agent_fallback
                        and target_agent_fallback.name in agent_schemas
                    ):
                        functions.append(agent_schemas[target_agent_fallback.name])
                        print(f"Used fallback schema for {target_agent_fallback.name}")

        # Create CommandAgent with workflow-specific configuration
        command_agent = CommandAgent(
            name=f"WorkflowCommandAgent_{workflow.name}",
            agent_id=uuid.uuid4(),
            system_prompt=command_agent_system_prompt,
            persona="Command Agent",
            functions=functions,
            routing_options={
                "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
                "respond": "If you think you have the answer, you can stop here.",
                "give_up": "If you think you can't answer the query, you can give up and let the user know.",
            },
            model="gpt-4o-mini",
            temperature=0.7,
            short_term_memory=True,
            long_term_memory=False,
            reasoning=False,
            input_type=["text", "voice"],
            output_type=["text", "voice"],
            response_type="json",
            max_retries=5,
            timeout=None,
            deployed=True,
            status="active",
            priority=None,
            failure_strategies=["retry", "escalate"],
            session_id=None,
            last_active=datetime.now(),
            collaboration_mode="single",
        )

        return command_agent

    def _create_workflow_deployment(
        self, db: Session, workflow, deployment
    ) -> Dict[str, Any]:
        """
        Create deployment based on workflow type (single-agent vs multi-agent)
        """
        agents = workflow.configuration.get("agents", [])

        if len(agents) == 1:
            # Single-agent workflow - deploy agent directly
            agent_config = agents[0]
            agent_type = agent_config.get("agent_type", "CommandAgent")

            if agent_type == "ToshibaAgent":
                # Create ToshibaAgent directly
                agent = self._build_toshiba_agent(db, workflow, agent_config)
                return {
                    "agent": agent,
                    "agent_type": "ToshibaAgent",
                    "deployment": deployment,
                    "workflow": workflow,
                    "deployed_at": datetime.now(),
                    "is_single_agent": True,
                }
            else:
                # Create other single agents directly
                agent = self._build_single_agent(db, workflow, agent_config)
                return {
                    "agent": agent,
                    "agent_type": agent_type,
                    "deployment": deployment,
                    "workflow": workflow,
                    "deployed_at": datetime.now(),
                    "is_single_agent": True,
                }
        else:
            # Multi-agent workflow - use CommandAgent
            command_agent = self._build_command_agent_from_workflow(db, workflow)
            return {
                "command_agent": command_agent,
                "agent_type": "CommandAgent",
                "deployment": deployment,
                "workflow": workflow,
                "deployed_at": datetime.now(),
                "is_single_agent": False,
            }

    def _build_toshiba_agent(self, db: Session, workflow, agent_config):
        """Build ToshibaAgent from configuration"""
        from agents.toshiba_agent import create_toshiba_agent
        from prompts import toshiba_agent_system_prompt
        from agents.tools import tool_schemas

        # Get ToshibaAgent-specific configuration
        functions = (
            [tool_schemas.get("query_retriever2")]
            if "query_retriever2" in tool_schemas
            else []
        )

        return create_toshiba_agent(
            system_prompt=toshiba_agent_system_prompt, functions=functions
        )

    def _build_single_agent(self, db: Session, workflow, agent_config):
        """Build a single agent from configuration"""
        # This can be extended for other single-agent types
        # For now, fall back to CommandAgent
        return self._build_command_agent_from_workflow(db, workflow)


# Global workflow service instance
workflow_service = WorkflowService()
