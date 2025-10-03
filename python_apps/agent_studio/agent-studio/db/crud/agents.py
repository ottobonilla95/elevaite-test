import uuid
from typing import List, Optional
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from sqlalchemy.orm import Session

from agents.tools import tool_schemas
from ..models import Agent
from ..schemas import AgentCreate, AgentUpdate


def validate_agent_functions(functions: List) -> List[ChatCompletionToolParam]:
    validated_functions = []
    for func in functions:
        if hasattr(func, "function") and hasattr(func.function, "name"):
            function_name = func.function.name
        elif isinstance(func, dict) and "function" in func:
            function_name = func["function"]["name"]
        else:
            continue

        if function_name in tool_schemas:
            # tool_schemas values are already dicts (ChatCompletionToolParam)
            validated_functions.append(tool_schemas[function_name])
        else:
            # Convert Pydantic model to dict if needed
            if hasattr(func, "model_dump"):
                validated_functions.append(func.model_dump())
            elif hasattr(func, "dict"):
                validated_functions.append(func.dict())
            else:
                validated_functions.append(func)
    return validated_functions


def create_agent(db: Session, agent: AgentCreate) -> Agent:
    validated_functions = validate_agent_functions(agent.functions)

    db_agent = Agent(
        name=agent.name,
        agent_type=agent.agent_type,
        description=agent.description,
        parent_agent_id=agent.parent_agent_id,
        system_prompt_id=agent.system_prompt_id,
        persona=agent.persona,
        functions=validated_functions,
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
        available_for_deployment=agent.available_for_deployment,
        deployment_code=agent.deployment_code,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_id: uuid.UUID) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.agent_id == agent_id).first()


def get_agent_by_id(db: Session, agent_id: uuid.UUID) -> Optional[Agent]:
    return get_agent(db, agent_id)


def get_agent_by_name(db: Session, name: str) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.name == name).first()


def get_agents(db: Session, skip: int = 0, limit: int = 100, deployed: Optional[bool] = None) -> List[Agent]:
    query = db.query(Agent)
    if deployed is not None:
        query = query.filter(Agent.deployed == deployed)
    return query.offset(skip).limit(limit).all()


def get_agents_by_type(db: Session, agent_type: str) -> List[Agent]:
    return db.query(Agent).filter(Agent.agent_type == agent_type).all()


def get_available_agents_for_deployment(db: Session) -> List[Agent]:
    return db.query(Agent).filter(Agent.available_for_deployment == True).all()


def get_deployed_agents(db: Session) -> List[Agent]:
    return db.query(Agent).filter(Agent.deployed == True).all()


def get_active_agents(db: Session) -> List[Agent]:
    return db.query(Agent).filter(Agent.status == "active").all()


def update_agent(db: Session, agent_id: uuid.UUID, agent_update: AgentUpdate) -> Optional[Agent]:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return None

    update_data = agent_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)

    if "functions" in update_data:
        setattr(db_agent, "functions", validate_agent_functions(update_data["functions"]))

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


def set_agent_deployment_status(db: Session, agent_id: uuid.UUID, deployed: bool) -> Optional[Agent]:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return None

    db_agent.deployed = deployed
    db.commit()
    db.refresh(db_agent)
    return db_agent


def set_agent_status(db: Session, agent_id: uuid.UUID, status: str) -> Optional[Agent]:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return None

    db_agent.status = status
    db.commit()
    db.refresh(db_agent)
    return db_agent


def update_agent_session(db: Session, agent_id: uuid.UUID, session_id: Optional[str]) -> Optional[Agent]:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return None

    db_agent.session_id = session_id
    if session_id:
        from datetime import datetime

        db_agent.last_active = datetime.now()

    db.commit()
    db.refresh(db_agent)
    return db_agent
