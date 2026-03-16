"""
Pydantic request schemas for memory endpoints.
"""

from pydantic import BaseModel, Field


class GlobalMemoryCreateRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    content_type: str = "text"
    tags: list[str] = Field(default_factory=list)


class GlobalMemoryUpdateRequest(BaseModel):
    key: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = None
    content_type: str | None = None
    tags: list[str] | None = None


class AgentMemoryCreateRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    importance: int = Field(3, ge=1, le=5)


class AgentMemoryUpdateRequest(BaseModel):
    content: str | None = None
    importance: int | None = Field(None, ge=1, le=5)


class TaskMemoryCreateRequest(BaseModel):
    summary: str = Field(..., min_length=1)
    key_facts: list[str] = Field(default_factory=list)
