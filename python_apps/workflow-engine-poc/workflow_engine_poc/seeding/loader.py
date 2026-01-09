"""
Seed Data Loader

Loads JSON seed data files and resolves cross-references between entities.
Maintains a mapping from template_ids to real UUIDs created during seeding.
"""

import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlmodel import Session

from workflow_core_sdk.services import PromptsService, AgentsService, ToolsService, WorkflowsService
from workflow_core_sdk.db.models import PromptCreate, ToolCreate

logger = logging.getLogger(__name__)

# Path to seed data files
SEED_DATA_DIR = Path(__file__).parent / "seed_data"


class SeedDataLoader:
    """
    Loads seed data from JSON files and creates entities in the database.

    Maintains mappings from template_ids to real UUIDs for cross-referencing:
    - prompt_ids: template_id -> UUID
    - tool_ids: template_id -> UUID
    - agent_ids: template_id -> UUID
    - workflow_ids: template_id -> UUID
    """

    def __init__(self, session: Session):
        self.session = session
        self.prompt_ids: dict[str, UUID] = {}
        self.tool_ids: dict[str, UUID] = {}
        self.agent_ids: dict[str, UUID] = {}
        self.workflow_ids: dict[str, UUID] = {}

    def _load_json(self, filename: str) -> dict[str, Any]:
        """Load a JSON file from the seed_data directory."""
        filepath = SEED_DATA_DIR / filename
        if not filepath.exists():
            logger.warning(f"Seed data file not found: {filepath}")
            return {}
        with open(filepath) as f:
            return json.load(f)

    def load_prompts(self) -> int:
        """Load prompts from prompts.json. Returns count of created prompts."""
        data = self._load_json("prompts.json")
        prompts = data.get("prompts", [])
        created = 0

        for prompt_data in prompts:
            template_id = prompt_data.pop("template_id", None)
            if not template_id:
                logger.warning("Prompt missing template_id, skipping")
                continue

            try:
                prompt_create = PromptCreate(**prompt_data)
                db_prompt = PromptsService.create_prompt(self.session, prompt_create)
                self.prompt_ids[template_id] = db_prompt.id
                created += 1
                logger.debug(f"Created prompt '{template_id}' with id {db_prompt.id}")
            except ValueError as e:
                # Likely duplicate - could happen if seeding runs twice
                logger.warning(f"Could not create prompt '{template_id}': {e}")
            except Exception as e:
                logger.error(f"Error creating prompt '{template_id}': {e}")

        logger.info(f"Loaded {created} prompts")
        return created

    def load_tools(self) -> int:
        """Load tools from tools.json. Returns count of created tools."""
        data = self._load_json("tools.json")
        tools = data.get("tools", [])
        created = 0

        for tool_data in tools:
            template_id = tool_data.pop("template_id", None)
            if not template_id:
                logger.warning("Tool missing template_id, skipping")
                continue

            try:
                tool_create = ToolCreate(**tool_data)
                db_tool = ToolsService.create_tool(self.session, tool_create)
                self.tool_ids[template_id] = db_tool.id
                created += 1
                logger.debug(f"Created tool '{template_id}' with id {db_tool.id}")
            except ValueError as e:
                logger.warning(f"Could not create tool '{template_id}': {e}")
            except Exception as e:
                logger.error(f"Error creating tool '{template_id}': {e}")

        logger.info(f"Loaded {created} tools")
        return created

    def load_agents(self) -> int:
        """Load agents from agents.json. Returns count of created agents."""
        data = self._load_json("agents.json")
        agents = data.get("agents", [])
        created = 0

        for agent_data in agents:
            template_id = agent_data.pop("template_id", None)
            if not template_id:
                logger.warning("Agent missing template_id, skipping")
                continue

            # Resolve prompt reference
            prompt_template_id = agent_data.pop("prompt_template_id", None)
            if prompt_template_id:
                prompt_uuid = self.prompt_ids.get(prompt_template_id)
                if prompt_uuid:
                    agent_data["system_prompt_id"] = prompt_uuid
                else:
                    logger.warning(f"Prompt '{prompt_template_id}' not found for agent '{template_id}'")
                    continue

            # Extract tool bindings for later
            tool_bindings = agent_data.pop("tool_bindings", [])

            try:
                db_agent = AgentsService.create_agent(self.session, agent_data)
                self.agent_ids[template_id] = db_agent.id
                created += 1
                logger.debug(f"Created agent '{template_id}' with id {db_agent.id}")

                # Create tool bindings
                for binding in tool_bindings:
                    tool_template_id = binding.get("tool_template_id")
                    if tool_template_id:
                        tool_uuid = self.tool_ids.get(tool_template_id)
                        if tool_uuid:
                            try:
                                AgentsService.attach_tool_to_agent(
                                    self.session,
                                    str(db_agent.id),
                                    tool_id=str(tool_uuid),
                                    is_active=binding.get("is_active", True),
                                )
                            except Exception as e:
                                logger.warning(f"Could not bind tool '{tool_template_id}' to agent: {e}")
            except ValueError as e:
                logger.warning(f"Could not create agent '{template_id}': {e}")
            except Exception as e:
                logger.error(f"Error creating agent '{template_id}': {e}")

        logger.info(f"Loaded {created} agents")
        return created

    def load_workflows(self) -> int:
        """Load workflows from workflows.json. Returns count of created workflows."""
        data = self._load_json("workflows.json")
        workflows = data.get("workflows", [])
        created = 0

        for workflow_data in workflows:
            template_id = workflow_data.pop("template_id", None)
            if not template_id:
                logger.warning("Workflow missing template_id, skipping")
                continue

            # Resolve agent references in steps if present
            steps = workflow_data.get("steps", [])
            for step in steps:
                params = step.get("parameters", {})
                agent_template_id = params.get("agent_template_id")
                if agent_template_id:
                    agent_uuid = self.agent_ids.get(agent_template_id)
                    if agent_uuid:
                        # Replace template_id with actual agent name or id
                        params["agent_id"] = str(agent_uuid)
                        del params["agent_template_id"]

            try:
                db_workflow = WorkflowsService.create_workflow(self.session, workflow_data)
                self.workflow_ids[template_id] = db_workflow.id
                created += 1
                logger.debug(f"Created workflow '{template_id}' with id {db_workflow.id}")
            except ValueError as e:
                logger.warning(f"Could not create workflow '{template_id}': {e}")
            except Exception as e:
                logger.error(f"Error creating workflow '{template_id}': {e}")

        logger.info(f"Loaded {created} workflows")
        return created

    def load_all(self) -> dict[str, int]:
        """Load all seed data in dependency order. Returns counts by entity type."""
        logger.info("Starting seed data loading...")

        results = {
            "prompts": self.load_prompts(),
            "tools": self.load_tools(),
            "agents": self.load_agents(),
            "workflows": self.load_workflows(),
        }

        total = sum(results.values())
        logger.info(f"Seed data loading complete. Created {total} entities: {results}")

        return results
