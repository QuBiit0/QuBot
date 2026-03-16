"""
Tool request schemas
"""

from uuid import UUID

from pydantic import BaseModel, Field

from ..models.enums import ToolTypeEnum


class ToolCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: ToolTypeEnum
    description: str = ""
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    is_dangerous: bool = False


class ToolUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None
    config: dict | None = None
    is_dangerous: bool | None = None


class ToolAssignRequest(BaseModel):
    tool_id: UUID
    permissions: str = "READ_ONLY"
