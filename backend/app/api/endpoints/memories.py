"""
Memories API Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...services import MemoryService

router = APIRouter()


# Global Memory endpoints

@router.get("/memories/global", response_model=dict)
async def list_global_memories(
    tags: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """List global memories with optional filters"""
    service = MemoryService(session)
    
    tag_list = tags.split(",") if tags else None
    memories = await service.get_global_memories(
        tags=tag_list,
        search_query=query,
        limit=limit,
    )
    
    return {"data": memories}


@router.post("/memories/global", response_model=dict)
async def create_global_memory(
    memory_data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a new global memory"""
    service = MemoryService(session)
    
    memory = await service.create_global_memory(
        key=memory_data["key"],
        content=memory_data["content"],
        content_type=memory_data.get("content_type", "text"),
        tags=memory_data.get("tags", []),
    )
    
    return {"data": memory}


@router.get("/memories/global/{memory_id}", response_model=dict)
async def get_global_memory(
    memory_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get global memory by ID"""
    service = MemoryService(session)
    memory = await service.get_global_memory(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"data": memory}


@router.put("/memories/global/{memory_id}", response_model=dict)
async def update_global_memory(
    memory_id: UUID,
    updates: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update global memory"""
    service = MemoryService(session)
    memory = await service.update_global_memory(memory_id, **updates)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"data": memory}


@router.delete("/memories/global/{memory_id}", response_model=dict)
async def delete_global_memory(
    memory_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Delete global memory"""
    service = MemoryService(session)
    success = await service.delete_global_memory(memory_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"message": "Memory deleted successfully"}


# Agent Memory endpoints

@router.get("/agents/{agent_id}/memories", response_model=dict)
async def get_agent_memories(
    agent_id: UUID,
    min_importance: int = Query(1, ge=1, le=5),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """Get all memories for an agent"""
    service = MemoryService(session)
    memories = await service.get_agent_memories(
        agent_id=agent_id,
        limit=limit,
        min_importance=min_importance,
    )
    
    return {"data": memories}


@router.post("/agents/{agent_id}/memories", response_model=dict)
async def create_agent_memory(
    agent_id: UUID,
    memory_data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a memory for an agent"""
    service = MemoryService(session)
    
    memory = await service.create_agent_memory(
        agent_id=agent_id,
        key=memory_data["key"],
        content=memory_data["content"],
        importance=memory_data.get("importance", 3),
    )
    
    return {"data": memory}


# Task Memory endpoints

@router.get("/tasks/{task_id}/memory", response_model=dict)
async def get_task_memory(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get memory associated with a task"""
    service = MemoryService(session)
    memory = await service.get_task_memory(task_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Task memory not found")
    
    return {"data": memory}


@router.post("/tasks/{task_id}/memory", response_model=dict)
async def create_task_memory(
    task_id: UUID,
    memory_data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a memory associated with a task"""
    service = MemoryService(session)
    
    memory = await service.create_task_memory(
        task_id=task_id,
        summary=memory_data["summary"],
        key_facts=memory_data.get("key_facts", []),
    )
    
    return {"data": memory}
