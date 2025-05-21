import uuid
import hashlib
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def create_prompt(db: Session, prompt: schemas.PromptCreate) -> models.Prompt:
    # Generate a hash if one isn't provided
    sha_hash = prompt.sha_hash
    if sha_hash is None:
        # Create a hash based on the prompt content, label, and timestamp
        content_to_hash = (
            f"{prompt.prompt}{prompt.prompt_label}{datetime.now().isoformat()}"
        )
        sha_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()[:40]

    db_prompt = models.Prompt(
        prompt_label=prompt.prompt_label,
        prompt=prompt.prompt,
        sha_hash=sha_hash,
        unique_label=prompt.unique_label,
        app_name=prompt.app_name,
        version=prompt.version,
        ai_model_provider=prompt.ai_model_provider,
        ai_model_name=prompt.ai_model_name,
        tags=prompt.tags,
        hyper_parameters=prompt.hyper_parameters,
        variables=prompt.variables,
        created_time=datetime.now(),
        is_deployed=False,
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def get_prompt(db: Session, prompt_id: uuid.UUID) -> Optional[models.Prompt]:
    return db.query(models.Prompt).filter(models.Prompt.pid == prompt_id).first()


def get_prompt_by_app_and_label(
    db: Session, app_name: str, prompt_label: str
) -> List[models.Prompt]:
    return (
        db.query(models.Prompt)
        .filter(
            models.Prompt.app_name == app_name,
            models.Prompt.prompt_label == prompt_label,
        )
        .all()
    )


def get_deployed_prompt(
    db: Session, app_name: str, prompt_label: str
) -> Optional[models.Prompt]:
    return (
        db.query(models.Prompt)
        .filter(
            models.Prompt.app_name == app_name,
            models.Prompt.prompt_label == prompt_label,
            models.Prompt.is_deployed == True,
        )
        .first()
    )


def get_prompts(
    db: Session, skip: int = 0, limit: int = 100, app_name: Optional[str] = None
) -> List[models.Prompt]:
    query = db.query(models.Prompt)
    if app_name:
        query = query.filter(models.Prompt.app_name == app_name)
    return query.offset(skip).limit(limit).all()


def update_prompt(
    db: Session, prompt_id: uuid.UUID, prompt_update: schemas.PromptUpdate
) -> Optional[models.Prompt]:
    db_prompt = get_prompt(db, prompt_id)
    if not db_prompt:
        return None

    update_data = prompt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)

    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def deploy_prompt(
    db: Session, prompt_id: uuid.UUID, app_name: str, environment: str = "production"
) -> Optional[models.Prompt]:
    db_prompt = get_prompt(db, prompt_id)
    if db_prompt is None or str(db_prompt.app_name) != app_name:
        return None

    prompt_label = str(db_prompt.prompt_label)
    currently_deployed = get_deployed_prompt(db, app_name, prompt_label)
    if currently_deployed is not None and str(currently_deployed.pid) != str(prompt_id):
        setattr(currently_deployed, "is_deployed", False)
        setattr(currently_deployed, "last_deployed", currently_deployed.deployed_time)

    setattr(db_prompt, "is_deployed", True)
    setattr(db_prompt, "deployed_time", datetime.now())
    setattr(db_prompt, "last_deployed", datetime.now())

    deployment = models.PromptDeployment(
        prompt_id=prompt_id,
        environment=environment,
        version_number=db_prompt.version,
        deployed_at=datetime.now(),
        is_active=True,
    )
    db.add(deployment)

    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def delete_prompt(db: Session, prompt_id: uuid.UUID) -> bool:
    db_prompt = get_prompt(db, prompt_id)
    if not db_prompt:
        return False

    db.delete(db_prompt)
    db.commit()
    return True


# Agent CRUD operations
def create_agent(db: Session, agent: schemas.AgentCreate) -> models.Agent:
    db_agent = models.Agent(
        name=agent.name,
        parent_agent_id=agent.parent_agent_id,
        system_prompt_id=agent.system_prompt_id,
        persona=agent.persona,
        functions=agent.functions,
        routing_options=agent.routing_options,
        short_term_memory=agent.short_term_memory,
        long_term_memory=agent.long_term_memory,
        reasoning=agent.reasoning,
        input_type=agent.input_type,
        output_type=agent.output_type,
        response_type=agent.response_type,
        max_retries=agent.max_retries,
        timeout=agent.timeout,
        deployed=agent.deployed,
        status=agent.status,
        priority=agent.priority,
        failure_strategies=agent.failure_strategies,
        collaboration_mode=agent.collaboration_mode,
        last_active=datetime.now(),
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_id: uuid.UUID) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.agent_id == agent_id).first()


def get_agent_by_name(db: Session, name: str) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.name == name).first()


def get_agents(
    db: Session, skip: int = 0, limit: int = 100, deployed: Optional[bool] = None
) -> List[models.Agent]:
    query = db.query(models.Agent)
    if deployed is not None:
        query = query.filter(models.Agent.deployed == deployed)
    return query.offset(skip).limit(limit).all()


def get_available_agents(db: Session) -> List[models.Agent]:
    return (
        db.query(models.Agent)
        .filter(models.Agent.available_for_deployment == True)
        .all()
    )


def get_agent_by_deployment_code(db: Session, code: str) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.deployment_code == code).first()


def update_agent(
    db: Session, agent_id: uuid.UUID, agent_update: schemas.AgentUpdate
) -> Optional[models.Agent]:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return None

    update_data = agent_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)

    db.commit()
    db.refresh(db_agent)
    return db_agent


def delete_agent(db: Session, agent_id: uuid.UUID) -> bool:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return False

    db.delete(db_agent)
    db.commit()
    return True
