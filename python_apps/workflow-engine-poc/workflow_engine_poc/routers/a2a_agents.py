"""
A2A Agents API router: CRUD for external A2A (Agent-to-Agent) protocol agents
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Security, Header
from fastapi.security.api_key import APIKeyHeader
from sqlmodel import Session

from workflow_engine_poc.util import api_key_or_user_guard

from workflow_core_sdk.db.database import get_db_session
from workflow_core_sdk.db.models import A2AAgentCreate, A2AAgentUpdate, A2AAgentRead
from workflow_core_sdk.db.models.a2a_agents import A2AAgent
from workflow_core_sdk.services import A2AAgentsService
from workflow_core_sdk.services.a2a_agents_service import A2AAgentsListQuery

from rbac_sdk import (
    HDR_API_KEY,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)

# Swagger/OpenAPI: expose API key header for testing in docs
api_key_header = APIKeyHeader(name=HDR_API_KEY, auto_error=False)

router = APIRouter(prefix="/a2a-agents", tags=["a2a-agents"])


def _build_agent_info(agent: A2AAgent):
    """Build A2AAgentInfo from database model."""
    from llm_gateway.a2a import A2AAgentInfo
    from llm_gateway.a2a.types import A2AAuthConfig

    auth_config = None
    if agent.auth_type != "none" and agent.auth_config:
        auth_config = A2AAuthConfig(auth_type=agent.auth_type, **agent.auth_config)

    return A2AAgentInfo(
        base_url=agent.base_url,
        name=agent.name,
        agent_card_url=agent.agent_card_url,
        auth=auth_config,
    )


# ---------- A2A Agents CRUD ----------
@router.post(
    "/",
    response_model=A2AAgentRead,
    dependencies=[Depends(api_key_or_user_guard("create_a2a_agent"))],
)
async def create_a2a_agent(
    agent: A2AAgentCreate,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Register a new external A2A agent.

    This endpoint registers an external agent that exposes the A2A protocol.
    The agent's Agent Card will be fetched and cached after registration.
    """
    try:
        return A2AAgentsService.create_agent(session, agent, created_by=user_id)
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))


@router.get(
    "/",
    response_model=List[A2AAgentRead],
    dependencies=[Depends(api_key_or_user_guard("view_a2a_agent"))],
)
async def list_a2a_agents(
    session: Session = Depends(get_db_session),
    organization_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """List registered A2A agents with optional filtering."""
    tags = [tag] if tag else None
    params = A2AAgentsListQuery(
        organization_id=organization_id,
        status=status,
        tags=tags,
        q=q,
        limit=limit,
        offset=offset,
    )
    return A2AAgentsService.list_agents(session, params)


@router.get(
    "/{agent_id}",
    response_model=A2AAgentRead,
    dependencies=[Depends(api_key_or_user_guard("view_a2a_agent"))],
)
async def get_a2a_agent(
    agent_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Get a single A2A agent by ID."""
    agent = A2AAgentsService.get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="A2A agent not found")
    return agent


@router.patch(
    "/{agent_id}",
    response_model=A2AAgentRead,
    dependencies=[Depends(api_key_or_user_guard("update_a2a_agent"))],
)
async def update_a2a_agent(
    agent_id: str,
    payload: A2AAgentUpdate,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Update an A2A agent's configuration."""
    try:
        return A2AAgentsService.update_agent(session, agent_id, payload)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.delete(
    "/{agent_id}", dependencies=[Depends(api_key_or_user_guard("delete_a2a_agent"))]
)
async def delete_a2a_agent(
    agent_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Delete an A2A agent registration."""
    deleted = A2AAgentsService.delete_agent(session, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="A2A agent not found")
    return {"status": "deleted", "agent_id": agent_id}


# ---------- A2A Agent Card & Health ----------
@router.post(
    "/{agent_id}/refresh-card",
    response_model=A2AAgentRead,
    dependencies=[Depends(api_key_or_user_guard("update_a2a_agent"))],
)
async def refresh_agent_card(
    agent_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Fetch and cache the Agent Card from the remote A2A agent."""
    from llm_gateway.a2a import A2AClientService

    agent = A2AAgentsService.get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="A2A agent not found")

    client_service = A2AClientService()
    try:
        card = await client_service.get_agent_card(
            _build_agent_info(agent), force_refresh=True
        )
        card_dict = card.model_dump()
    except Exception as e:
        A2AAgentsService.update_health_status(
            session, agent_id, is_healthy=False, error_message=str(e)
        )
        raise HTTPException(status_code=502, detail=f"Failed to fetch Agent Card: {e}")

    updated_agent = A2AAgentsService.update_agent_card(session, agent_id, card_dict)
    A2AAgentsService.update_health_status(session, agent_id, is_healthy=True)
    return updated_agent


@router.post(
    "/{agent_id}/health-check",
    response_model=A2AAgentRead,
    dependencies=[Depends(api_key_or_user_guard("view_a2a_agent"))],
)
async def check_agent_health(
    agent_id: str,
    session: Session = Depends(get_db_session),
    # RBAC headers for Swagger UI testing
    api_key: Optional[str] = Security(api_key_header),
    user_id: Optional[str] = Header(default=None, alias=HDR_USER_ID),
    org_id: Optional[str] = Header(default=None, alias=HDR_ORG_ID),
    project_id: Optional[str] = Header(default=None, alias=HDR_PROJECT_ID),
    account_id: Optional[str] = Header(default=None, alias=HDR_ACCOUNT_ID),
):
    """Perform a health check on an A2A agent by attempting to fetch its Agent Card."""
    from llm_gateway.a2a import A2AClientService

    agent = A2AAgentsService.get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="A2A agent not found")

    client_service = A2AClientService()
    try:
        await client_service.get_agent_card(
            _build_agent_info(agent), force_refresh=True
        )
        is_healthy, error_message = True, None
    except Exception as e:
        is_healthy, error_message = False, str(e)

    return A2AAgentsService.update_health_status(
        session, agent_id, is_healthy=is_healthy, error_message=error_message
    )
