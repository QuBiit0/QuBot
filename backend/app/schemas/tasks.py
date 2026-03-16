"""
Task request/response schemas
"""

from uuid import UUID

from pydantic import BaseModel, Field

from ..models.enums import PriorityEnum, TaskStatusEnum


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    priority: PriorityEnum = PriorityEnum.MEDIUM
    domain_hint: str | None = None
    assigned_agent_id: UUID | None = None
    parent_task_id: UUID | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    priority: PriorityEnum | None = None
    domain_hint: str | None = None


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatusEnum
    agent_id: UUID | None = None


class TaskAssignRequest(BaseModel):
    agent_id: UUID


class TaskEventRequest(BaseModel):
    event_type: str
    payload: dict = Field(default_factory=dict)
    agent_id: UUID | None = None


class SubtaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    priority: PriorityEnum = PriorityEnum.MEDIUM
