from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db import models, crud
from db.fixtures import DEFAULT_PROMPTS, DEFAULT_AGENTS, AGENT_CODES
from services.demo_service import DemoInitializationService
from .demo_schemas import DemoInitializationResponse, DemoStatusResponse

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/initialize", response_model=DemoInitializationResponse)
def initialize_demo_data(db: Session = Depends(get_db)):
    service = DemoInitializationService(db)
    success, message, details = service.initialize_all()

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return DemoInitializationResponse(success=success, message=message, details=details)


@router.post("/initialize/prompts", response_model=DemoInitializationResponse)
def initialize_demo_prompts(db: Session = Depends(get_db)):
    service = DemoInitializationService(db)
    success, message, details = service.initialize_prompts()

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return DemoInitializationResponse(
        success=success, message=message, details={"prompts": details}
    )


@router.post("/initialize/agents", response_model=DemoInitializationResponse)
def initialize_demo_agents(db: Session = Depends(get_db)):
    service = DemoInitializationService(db)
    success, message, details = service.initialize_agents()

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return DemoInitializationResponse(
        success=success, message=message, details={"agents": details}
    )


@router.get("/status", response_model=DemoStatusResponse)
def get_demo_status(db: Session = Depends(get_db)):
    prompts_count = 0
    for prompt_data in DEFAULT_PROMPTS:
        existing_prompt = (
            db.query(models.Prompt)
            .filter(models.Prompt.unique_label == prompt_data.unique_label)
            .first()
        )
        if existing_prompt:
            prompts_count += 1

    agents_count = 0
    for agent_data in DEFAULT_AGENTS:
        existing_agent = (
            db.query(models.Agent).filter(models.Agent.name == agent_data.name).first()
        )
        if existing_agent:
            agents_count += 1

    available_agents = crud.get_available_agents(db)
    deployment_codes = {}
    for agent in available_agents:
        deployment_code = getattr(agent, "deployment_code", None)
        if deployment_code is not None and str(deployment_code).strip() != "":
            deployment_codes[str(deployment_code)] = str(agent.name)

    return DemoStatusResponse(
        prompts_initialized=prompts_count == len(DEFAULT_PROMPTS),
        agents_initialized=agents_count == len(DEFAULT_AGENTS),
        total_prompts=prompts_count,
        total_agents=agents_count,
        available_deployment_codes=deployment_codes,
    )


@router.get("/info")
def get_demo_info():
    return {
        "available_prompts": [
            {
                "label": prompt.prompt_label,
                "unique_label": prompt.unique_label,
                "description": (
                    prompt.prompt[:100] + "..."
                    if len(prompt.prompt) > 100
                    else prompt.prompt
                ),
            }
            for prompt in DEFAULT_PROMPTS
        ],
        "available_agents": [
            {
                "name": agent.name,
                "persona": agent.persona,
                "deployment_code": AGENT_CODES.get(agent.name),
                "capabilities": {
                    "short_term_memory": agent.short_term_memory,
                    "long_term_memory": agent.long_term_memory,
                    "reasoning": agent.reasoning,
                },
            }
            for agent in DEFAULT_AGENTS
        ],
        "deployment_codes": AGENT_CODES,
    }
