from datetime import datetime

from pydantic import BaseModel

from .models.enums import AgentStatusEnum, DomainEnum, TaskStatusEnum


# Agent Schemas
class AgentBase(BaseModel):
    name: str
    role: str
    skill: str
    domain: DomainEnum = DomainEnum.GENERAL
    status: AgentStatusEnum = AgentStatusEnum.OFFLINE
    avatar_url: str | None = None


class AgentCreate(AgentBase):
    system_prompt: str | None = None


class AgentUpdate(BaseModel):
    status: AgentStatusEnum | None = None
    avatar_url: str | None = None


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
    agent_id: int | None = None
    parent_task_id: int | None = None


class TaskCreate(TaskBase):
    input_data: dict | None = None


class TaskUpdate(BaseModel):
    status: TaskStatusEnum | None = None
    output_data: dict | None = None
    completed_at: datetime | None = None


class TaskInDB(TaskBase):
    id: int
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True
