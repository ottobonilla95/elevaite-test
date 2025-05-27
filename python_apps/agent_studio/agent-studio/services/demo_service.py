import uuid
import sqlalchemy
from typing import Dict, Tuple
from sqlalchemy.orm import Session

from db import models, schemas, crud
from db.fixtures import DEFAULT_PROMPTS, DEFAULT_AGENTS, AGENT_CODES
from db.database import engine


class DemoInitializationService:
    def __init__(self, db: Session):
        self.db = db

    def initialize_prompts(self) -> Tuple[bool, str, Dict]:
        try:
            inspector = sqlalchemy.inspect(engine)
            if not inspector.has_table("prompts"):
                return (
                    False,
                    "The prompts table does not exist. Please run database migrations first.",
                    {},
                )

            added_count = 0
            skipped_count = 0
            added_prompts = []

            for prompt_data in DEFAULT_PROMPTS:
                existing_prompt = (
                    self.db.query(models.Prompt)
                    .filter(models.Prompt.unique_label == prompt_data.unique_label)
                    .first()
                )

                if existing_prompt is None:
                    prompt_create = schemas.PromptCreate(
                        prompt_label=prompt_data.prompt_label,
                        prompt=prompt_data.prompt,
                        unique_label=prompt_data.unique_label,
                        app_name=prompt_data.app_name,
                        version=prompt_data.version,
                        ai_model_provider=prompt_data.ai_model_provider,
                        ai_model_name=prompt_data.ai_model_name,
                        tags=prompt_data.tags,
                        hyper_parameters=prompt_data.hyper_parameters,
                        variables=prompt_data.variables,
                    )

                    crud.create_prompt(db=self.db, prompt=prompt_create)
                    added_prompts.append(prompt_data.prompt_label)
                    added_count += 1
                else:
                    skipped_count += 1

            if added_count > 0:
                self.db.commit()

            return (
                True,
                f"Successfully processed {len(DEFAULT_PROMPTS)} prompts: {added_count} added, {skipped_count} already existed.",
                {
                    "added_count": added_count,
                    "skipped_count": skipped_count,
                    "added_prompts": added_prompts,
                },
            )

        except Exception as e:
            self.db.rollback()
            return False, f"Error initializing prompts: {str(e)}", {}

    def initialize_agents(self) -> Tuple[bool, str, Dict]:
        try:
            inspector = sqlalchemy.inspect(engine)
            if not inspector.has_table("agents"):
                return (
                    False,
                    "The agents table does not exist. Please run database migrations first.",
                    {},
                )

            added_count = 0
            updated_count = 0
            skipped_count = 0
            added_agents = []
            updated_agents = []

            for agent_data in DEFAULT_AGENTS:
                existing_agent = (
                    self.db.query(models.Agent)
                    .filter(models.Agent.name == agent_data.name)
                    .first()
                )

                if existing_agent is None:
                    # Check if the required prompt exists
                    prompt = (
                        self.db.query(models.Prompt)
                        .filter(models.Prompt.unique_label == agent_data.prompt_label)
                        .first()
                    )

                    if prompt is None:
                        return (
                            False,
                            f"Required prompt '{agent_data.prompt_label}' not found. Please initialize prompts first.",
                            {},
                        )

                    deployment_code = AGENT_CODES.get(agent_data.name)
                    prompt_id = uuid.UUID(str(prompt.pid))

                    agent_create = schemas.AgentCreate(
                        name=agent_data.name,
                        system_prompt_id=prompt_id,
                        persona=agent_data.persona,
                        functions=agent_data.functions,
                        routing_options=agent_data.routing_options,
                        short_term_memory=agent_data.short_term_memory,
                        long_term_memory=agent_data.long_term_memory,
                        reasoning=agent_data.reasoning,
                        input_type=agent_data.input_type,
                        output_type=agent_data.output_type,
                        response_type=agent_data.response_type,
                        max_retries=agent_data.max_retries,
                        timeout=agent_data.timeout,
                        deployed=agent_data.deployed,
                        status=agent_data.status,
                        priority=agent_data.priority,
                        failure_strategies=agent_data.failure_strategies,
                        collaboration_mode=agent_data.collaboration_mode,
                        deployment_code=deployment_code,
                        available_for_deployment=True,
                    )

                    crud.create_agent(db=self.db, agent=agent_create)
                    added_agents.append(f"{agent_data.name} (code: {deployment_code})")
                    added_count += 1
                else:
                    # Check if we need to update deployment code
                    existing_code = getattr(existing_agent, "deployment_code", None)
                    has_code = (
                        existing_code is not None and str(existing_code).strip() != ""
                    )
                    deployment_code = AGENT_CODES.get(agent_data.name)

                    if not has_code and deployment_code is not None:
                        setattr(existing_agent, "deployment_code", deployment_code)
                        setattr(existing_agent, "available_for_deployment", True)
                        updated_agents.append(
                            f"{agent_data.name} (added code: {deployment_code})"
                        )
                        updated_count += 1
                    else:
                        skipped_count += 1

            if added_count > 0 or updated_count > 0:
                self.db.commit()

            return (
                True,
                f"Successfully processed {len(DEFAULT_AGENTS)} agents: {added_count} added, {updated_count} updated, {skipped_count} already existed.",
                {
                    "added_count": added_count,
                    "updated_count": updated_count,
                    "skipped_count": skipped_count,
                    "added_agents": added_agents,
                    "updated_agents": updated_agents,
                },
            )

        except Exception as e:
            self.db.rollback()
            return False, f"Error initializing agents: {str(e)}", {}

    def initialize_all(self) -> Tuple[bool, str, Dict]:
        prompts_success, prompts_message, prompts_details = self.initialize_prompts()
        if not prompts_success:
            return (
                False,
                f"Failed to initialize prompts: {prompts_message}",
                {"prompts": prompts_details},
            )

        agents_success, agents_message, agents_details = self.initialize_agents()
        if not agents_success:
            return (
                False,
                f"Failed to initialize agents: {agents_message}",
                {"prompts": prompts_details, "agents": agents_details},
            )

        return (
            True,
            "Successfully initialized demo data.",
            {"prompts": prompts_details, "agents": agents_details},
        )
