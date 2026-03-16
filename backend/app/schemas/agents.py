"""
Agent request/response schemas
"""

from uuid import UUID

from pydantic import BaseModel, Field

from ..models.enums import AgentStatusEnum, DomainEnum


class ToolAssignmentRequest(BaseModel):
    tool_id: UUID
    permissions: str = "READ_ONLY"


class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., min_length=1, max_length=20)
    class_id: UUID
    domain: DomainEnum = DomainEnum.GENERAL
    role_description: str = ""
    personality: dict = Field(default_factory=dict)
    llm_config_id: UUID
    avatar_config: dict = Field(default_factory=dict)
    is_orchestrator: bool = False
    tool_assignments: list[ToolAssignmentRequest] = Field(default_factory=list)


class AgentUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    role_description: str | None = None
    personality: dict | None = None
    avatar_config: dict | None = None
    domain: DomainEnum | None = None


class AgentStatusUpdateRequest(BaseModel):
    status: AgentStatusEnum
    current_task_id: UUID | None = None


class AgentClassCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    domain: DomainEnum = DomainEnum.GENERAL
    default_avatar_config: dict = Field(default_factory=dict)
