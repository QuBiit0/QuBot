"""
Pydantic request schemas for tool execution endpoints.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from .llm_configs import ChatMessage


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., min_length=1)
    params: dict = Field(default_factory=dict)
    agent_id: UUID | None = None
    task_id: UUID | None = None


class LlmToolsExecuteRequest(BaseModel):
    llm_config_id: UUID
    messages: list[ChatMessage] = Field(..., min_length=1)
    system_prompt: str | None = None
    max_iterations: int = Field(5, ge=1, le=20)
    agent_id: UUID | None = None
    task_id: UUID | None = None


class TaskToolsExecuteRequest(BaseModel):
    llm_config_id: UUID
    system_prompt: str | None = None
    max_iterations: int = Field(5, ge=1, le=20)
