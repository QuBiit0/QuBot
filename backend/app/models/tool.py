"""
Tool model - Registry of available tools/skills
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import JSON, Index
from .enums import ToolTypeEnum


class Tool(SQLModel, table=True):
    """Registry of available tools/skills that agents can use"""
    __tablename__ = "tool"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    type: ToolTypeEnum = Field(index=True)
    description: str = Field(max_length=1000)  # Used verbatim in LLM prompts
    # JSON Schema (OpenAI function_call compatible)
    input_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    output_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Type-specific config: HTTP base_url/auth, Shell allowed_cmds, etc.
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    is_dangerous: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    agent_assignments: List["AgentTool"] = Relationship(back_populates="tool")
    
    __table_args__ = (
        Index("idx_tool_type", "type"),
    )
