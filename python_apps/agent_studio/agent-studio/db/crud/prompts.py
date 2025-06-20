import uuid
import hashlib
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Prompt, PromptVersion, PromptDeployment
from ..schemas import PromptCreate, PromptUpdate

def get_prompt_by_constraint(db: Session, app_name: str, prompt_label: str, version: str) -> Optional[Prompt]:
    return (
        db.query(Prompt)
        .filter(
            Prompt.app_name == app_name,
            Prompt.prompt_label == prompt_label,
            Prompt.version == version,
        )
        .first()
    )

def create_prompt_safe(db: Session, prompt: PromptCreate) -> Optional[Prompt]:
    existing = get_prompt_by_constraint(db, prompt.app_name, prompt.prompt_label, prompt.version)
    if existing:
        return existing

    return create_prompt(db, prompt)

def create_prompt(db: Session, prompt: PromptCreate) -> Prompt:
    sha_hash = prompt.sha_hash
    if sha_hash is None:
        content_to_hash = f"{prompt.prompt}{prompt.prompt_label}{datetime.now().isoformat()}"
        sha_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()[:40]

    db_prompt = Prompt(
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

def get_prompt(db: Session, prompt_id: uuid.UUID) -> Optional[Prompt]:
    return db.query(Prompt).filter(Prompt.pid == prompt_id).first()

def get_prompt_by_pid(db: Session, prompt_id: uuid.UUID) -> Optional[Prompt]:
    return get_prompt(db, prompt_id)

def get_prompt_by_app_and_label(db: Session, app_name: str, prompt_label: str) -> List[Prompt]:
    return (
        db.query(Prompt)
        .filter(
            Prompt.app_name == app_name,
            Prompt.prompt_label == prompt_label,
        )
        .all()
    )

def get_prompt_by_unique_label(db: Session, unique_label: str) -> Optional[Prompt]:
    return db.query(Prompt).filter(Prompt.unique_label == unique_label).first()

def get_deployed_prompt(db: Session, app_name: str, prompt_label: str) -> Optional[Prompt]:
    return (
        db.query(Prompt)
        .filter(
            Prompt.app_name == app_name,
            Prompt.prompt_label == prompt_label,
            Prompt.is_deployed,
        )
        .first()
    )

def get_prompts(db: Session, skip: int = 0, limit: int = 100, app_name: Optional[str] = None) -> List[Prompt]:
    query = db.query(Prompt)
    if app_name:
        query = query.filter(Prompt.app_name == app_name)
    return query.offset(skip).limit(limit).all()

def update_prompt(db: Session, prompt_id: uuid.UUID, prompt_update: PromptUpdate) -> Optional[Prompt]:
    db_prompt = get_prompt(db, prompt_id)
    if not db_prompt:
        return None

    update_data = prompt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)

    db.commit()
    db.refresh(db_prompt)
    return db_prompt

def deploy_prompt(db: Session, prompt_id: uuid.UUID, app_name: str, environment: str = "production") -> Optional[Prompt]:
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

    deployment = PromptDeployment(
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

def create_prompt_version(db: Session, version_data: dict) -> PromptVersion:
    db_version = PromptVersion(**version_data)
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

def get_prompt_versions(db: Session, prompt_id: uuid.UUID) -> List[PromptVersion]:
    return db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id).all()

def create_prompt_deployment(db: Session, deployment_data: dict) -> PromptDeployment:
    db_deployment = PromptDeployment(**deployment_data)
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)
    return db_deployment

def get_prompt_deployments(db: Session, prompt_id: Optional[uuid.UUID] = None, environment: Optional[str] = None) -> List[PromptDeployment]:
    query = db.query(PromptDeployment)
    if prompt_id:
        query = query.filter(PromptDeployment.prompt_id == prompt_id)
    if environment:
        query = query.filter(PromptDeployment.environment == environment)
    return query.all()
