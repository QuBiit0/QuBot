"""
Pydantic request schemas for execution endpoints.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from ..models.enums import DomainEnum, PriorityEnum


class ExecuteTaskRequest(BaseModel):
    max_iterations: int = Field(10, ge=1, le=100)


class OrchestratorProcessRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    llm_config_id: UUID
    priority: PriorityEnum = PriorityEnum.MEDIUM
    domain: DomainEnum | None = None
    input_data: dict | None = None


class AutoAssignRequest(BaseModel):
    force: bool = False
