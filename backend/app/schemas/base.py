from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from .models.enums import DomainEnum, AgentStatusEnum, TaskStatusEnum, MemoryScopeEnum

# Agent Schemas
class AgentBase(BaseModel):
    name: str
    role: str
    skill: str
    domain: DomainEnum = DomainEnum.GENERAL
    status: AgentStatusEnum = AgentStatusEnum.OFFLINE
    avatar_url: Optional[str] = None

class AgentCreate(AgentBase):
    system_prompt: Optional[str] = None

class AgentUpdate(BaseModel):
    status: Optional[AgentStatusEnum] = None
    avatar_url: Optional[str] = None

class AgentInDB(AgentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: str
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    priority: int = 0
    agent_id: Optional[int] = None
    parent_task_id: Optional[int] = None

class TaskCreate(TaskBase):
    input_data: Optional[dict] = None

class TaskUpdate(BaseModel):
    status: Optional[TaskStatusEnum] = None
    output_data: Optional[dict] = None
    completed_at: Optional[datetime] = None

class TaskInDB(TaskBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
