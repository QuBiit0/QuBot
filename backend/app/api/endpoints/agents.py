"""
Agents API Endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import get_current_user
from ...database import get_session
from ...models.enums import AgentStatusEnum
from ...models.user import User
from ...schemas.agents import (
    AgentClassCreateRequest,
    AgentCreateRequest,
    AgentStatusUpdateRequest,
    AgentUpdateRequest,
)
from ...services import AgentService

router = APIRouter()


@router.get("/agents", response_model=None)
async def list_agents(
    status: AgentStatusEnum | None = None,
    domain: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List all agents with optional filters"""
    service = AgentService(session)
    agents, total = await service.get_agents_with_count(
        status=status, domain=domain, skip=skip, limit=limit
    )

    return {
        "data": agents,
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }


@router.post("/agents", response_model=None, status_code=201)
async def create_agent(
    agent_data: AgentCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new agent"""
    service = AgentService(session)

    agent = await service.create_agent(
        name=agent_data.name,
        gender=agent_data.gender,
        class_id=agent_data.class_id,
        domain=agent_data.domain,
        role_description=agent_data.role_description,
        personality=agent_data.personality,
        llm_config_id=agent_data.llm_config_id,
        avatar_config=agent_data.avatar_config,
        is_orchestrator=agent_data.is_orchestrator,
    )

    # Assign tools if provided
    for assignment in agent_data.tool_assignments:
        await service.assign_tool(
            agent_id=agent.id,
            tool_id=assignment.tool_id,
            permissions=assignment.permissions,
        )

    return {"data": agent}


@router.get("/agents/{agent_id}", response_model=None)
async def get_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get agent by ID"""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tools = await service.get_agent_tools(agent_id)

    return {
        "data": {
            **agent.__dict__,
            "tools": tools,
        },
    }


@router.put("/agents/{agent_id}", response_model=None)
async def update_agent(
    agent_id: UUID,
    updates: AgentUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update agent"""
    service = AgentService(session)
    agent = await service.update_agent(
        agent_id, **updates.model_dump(exclude_none=True)
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"data": agent}


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Soft delete agent (set status to OFFLINE)"""
    service = AgentService(session)
    success = await service.delete_agent(agent_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.patch("/agents/{agent_id}/status", response_model=None)
async def update_agent_status(
    agent_id: UUID,
    status_update: AgentStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update agent status"""
    service = AgentService(session)

    agent = await service.update_agent_status(
        agent_id=agent_id,
        status=status_update.status,
        current_task_id=status_update.current_task_id,
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"data": agent}


# ── Agent Classes ─────────────────────────────────────────────────────────────


@router.get("/agent-classes", response_model=None)
async def list_agent_classes(
    domain: str | None = None,
    is_custom: bool | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List agent classes"""
    service = AgentService(session)
    classes = await service.get_agent_classes(domain=domain, is_custom=is_custom)

    return {"data": classes}


@router.post("/agent-classes", response_model=None, status_code=201)
async def create_agent_class(
    class_data: AgentClassCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a custom agent class"""
    service = AgentService(session)

    agent_class = await service.create_agent_class(
        name=class_data.name,
        description=class_data.description,
        domain=class_data.domain,
        default_avatar_config=class_data.default_avatar_config,
    )

    return {"data": agent_class}


@router.get("/agent-classes/{class_id}", response_model=None)
async def get_agent_class(
    class_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get agent class by ID"""
    service = AgentService(session)
    agent_class = await service.get_agent_class(class_id)

    if not agent_class:
        raise HTTPException(status_code=404, detail="Agent class not found")

    return {"data": agent_class}
