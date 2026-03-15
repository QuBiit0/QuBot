"""
Agents API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...services import AgentService
from ...models.agent import Agent, AgentClass
from ...models.enums import AgentStatusEnum

router = APIRouter()


@router.get("/agents", response_model=dict)
async def list_agents(
    status: Optional[AgentStatusEnum] = None,
    domain: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List all agents with optional filters"""
    service = AgentService(session)
    agents = await service.get_agents(status=status, domain=domain, skip=skip, limit=limit)
    
    return {
        "data": agents,
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": len(agents),  # Note: Should use count query for real total
        },
    }


@router.post("/agents", response_model=dict)
async def create_agent(
    agent_data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a new agent"""
    service = AgentService(session)
    
    agent = await service.create_agent(
        name=agent_data["name"],
        gender=agent_data["gender"],
        class_id=UUID(agent_data["class_id"]),
        domain=agent_data["domain"],
        role_description=agent_data.get("role_description", ""),
        personality=agent_data.get("personality", {}),
        llm_config_id=UUID(agent_data["llm_config_id"]),
        avatar_config=agent_data.get("avatar_config", {}),
        is_orchestrator=agent_data.get("is_orchestrator", False),
    )
    
    # Assign tools if provided
    if "tool_assignments" in agent_data:
        for assignment in agent_data["tool_assignments"]:
            await service.assign_tool(
                agent_id=agent.id,
                tool_id=UUID(assignment["tool_id"]),
                permissions=assignment.get("permissions", "READ_ONLY"),
            )
    
    return {"data": agent}


@router.get("/agents/{agent_id}", response_model=dict)
async def get_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get agent by ID"""
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get agent tools
    tools = await service.get_agent_tools(agent_id)
    
    return {
        "data": {
            **agent.__dict__,
            "tools": tools,
        },
    }


@router.put("/agents/{agent_id}", response_model=dict)
async def update_agent(
    agent_id: UUID,
    updates: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update agent"""
    service = AgentService(session)
    agent = await service.update_agent(agent_id, **updates)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"data": agent}


@router.delete("/agents/{agent_id}", response_model=dict)
async def delete_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Soft delete agent (set status to OFFLINE)"""
    service = AgentService(session)
    success = await service.delete_agent(agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": "Agent deleted successfully"}


@router.patch("/agents/{agent_id}/status", response_model=dict)
async def update_agent_status(
    agent_id: UUID,
    status_update: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update agent status"""
    service = AgentService(session)
    
    current_task_id = status_update.get("current_task_id")
    if current_task_id:
        current_task_id = UUID(current_task_id)
    
    agent = await service.update_agent_status(
        agent_id=agent_id,
        status=AgentStatusEnum(status_update["status"]),
        current_task_id=current_task_id,
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"data": agent}


# Agent Classes endpoints

@router.get("/agent-classes", response_model=dict)
async def list_agent_classes(
    domain: Optional[str] = None,
    is_custom: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
):
    """List agent classes"""
    service = AgentService(session)
    classes = await service.get_agent_classes(domain=domain, is_custom=is_custom)
    
    return {"data": classes}


@router.post("/agent-classes", response_model=dict)
async def create_agent_class(
    class_data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a custom agent class"""
    service = AgentService(session)
    
    agent_class = await service.create_agent_class(
        name=class_data["name"],
        description=class_data.get("description", ""),
        domain=class_data["domain"],
        default_avatar_config=class_data.get("default_avatar_config", {}),
    )
    
    return {"data": agent_class}


@router.get("/agent-classes/{class_id}", response_model=dict)
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
