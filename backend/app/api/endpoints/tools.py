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
from ...schemas.tools import ToolAssignRequest, ToolCreateRequest, ToolUpdateRequest
from ...services import ToolService

router = APIRouter()


@router.get("/tools", response_model=None)
async def list_tools(
    tool_type: ToolTypeEnum | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List all tools with optional filters"""
    service = ToolService(session)
    tools = await service.get_tools(tool_type=tool_type, skip=skip, limit=limit)
    total = await service.count_tools(tool_type=tool_type)

    return {
        "data": tools,
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }


@router.post("/tools", response_model=None, status_code=201)
async def create_tool(
    tool_data: ToolCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new custom tool"""
    service = ToolService(session)

    tool = await service.create_tool(
        name=tool_data.name,
        tool_type=tool_data.type,
        description=tool_data.description,
        input_schema=tool_data.input_schema,
        output_schema=tool_data.output_schema,
        config=tool_data.config,
        is_dangerous=tool_data.is_dangerous,
    )

    return {"data": tool}


@router.get("/tools/{tool_id}", response_model=None)
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


@router.put("/tools/{tool_id}", response_model=None)
async def update_tool(
    tool_id: UUID,
    updates: ToolUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update tool"""
    service = ToolService(session)
    tool = await service.update_tool(tool_id, **updates.model_dump(exclude_none=True))

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {"data": tool}


@router.delete("/tools/{tool_id}", status_code=204)
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


@router.get("/tool-types", response_model=None)
async def list_tool_types():
    """List all available tool types"""
    types = [
        {"id": tt.value, "name": tt.name.replace("_", " ").title()}
        for tt in ToolTypeEnum
    ]
    return {"data": types}


@router.get("/agents/{agent_id}/tools", response_model=None)
async def get_agent_tools(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get all tools assigned to an agent"""
    from ...services import AgentService

    service = AgentService(session)
    tools = await service.get_agent_tools(agent_id)
    return {"data": tools}


@router.post("/agents/{agent_id}/tools", response_model=None, status_code=201)
async def assign_tool_to_agent(
    agent_id: UUID,
    assignment_data: ToolAssignRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Assign a tool to an agent"""
    from ...services import AgentService

    service = AgentService(session)
    assignment = await service.assign_tool(
        agent_id=agent_id,
        tool_id=assignment_data.tool_id,
        permissions=assignment_data.permissions,
    )
    return {"data": assignment}


@router.delete("/agents/{agent_id}/tools/{tool_id}", status_code=204)
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
