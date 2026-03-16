"""
Tools API Endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import get_current_user
from ...database import get_session
from ...models.enums import ToolTypeEnum
from ...models.user import User
from ...services import ToolService

router = APIRouter()


@router.get("/tools", response_model=dict)
async def list_tools(
    tool_type: ToolTypeEnum | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List all tools with optional filters"""
    service = ToolService(session)
    tools = await service.get_tools(
        tool_type=tool_type,
        skip=skip,
        limit=limit,
    )

    return {
        "data": tools,
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": len(tools),
        },
    }


@router.post("/tools", response_model=dict)
async def create_tool(
    tool_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new custom tool"""
    service = ToolService(session)

    tool = await service.create_tool(
        name=tool_data["name"],
        tool_type=ToolTypeEnum(tool_data["type"]),
        description=tool_data.get("description", ""),
        input_schema=tool_data.get("input_schema", {}),
        output_schema=tool_data.get("output_schema", {}),
        config=tool_data.get("config", {}),
        is_dangerous=tool_data.get("is_dangerous", False),
    )

    return {"data": tool}


@router.get("/tools/{tool_id}", response_model=dict)
async def get_tool(
    tool_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get tool by ID"""
    service = ToolService(session)
    tool = await service.get_tool(tool_id)

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {"data": tool}


@router.put("/tools/{tool_id}", response_model=dict)
async def update_tool(
    tool_id: UUID,
    updates: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update tool"""
    service = ToolService(session)
    tool = await service.update_tool(tool_id, **updates)

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {"data": tool}


@router.delete("/tools/{tool_id}", response_model=dict)
async def delete_tool(
    tool_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete tool"""
    service = ToolService(session)
    success = await service.delete_tool(tool_id)

    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {"message": "Tool deleted successfully"}


# Tool types


@router.get("/tool-types", response_model=dict)
async def list_tool_types():
    """List all available tool types"""
    types = [
        {"id": tt.value, "name": tt.name.replace("_", " ").title()}
        for tt in ToolTypeEnum
    ]

    return {"data": types}


# Agent tool assignments


@router.get("/agents/{agent_id}/tools", response_model=dict)
async def get_agent_tools(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get all tools assigned to an agent"""
    from ...services import AgentService

    service = AgentService(session)
    tools = await service.get_agent_tools(agent_id)

    return {"data": tools}


@router.post("/agents/{agent_id}/tools", response_model=dict)
async def assign_tool_to_agent(
    agent_id: UUID,
    assignment_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Assign a tool to an agent"""
    from ...services import AgentService

    service = AgentService(session)

    assignment = await service.assign_tool(
        agent_id=agent_id,
        tool_id=UUID(assignment_data["tool_id"]),
        permissions=assignment_data.get("permissions", "READ_ONLY"),
    )

    return {"data": assignment}


@router.delete("/agents/{agent_id}/tools/{tool_id}", response_model=dict)
async def remove_tool_from_agent(
    agent_id: UUID,
    tool_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a tool assignment from an agent"""
    from ...services import AgentService

    service = AgentService(session)
    success = await service.unassign_tool(agent_id=agent_id, tool_id=tool_id)

    if not success:
        raise HTTPException(status_code=404, detail="Tool assignment not found")

    return {"message": "Tool unassigned successfully"}
