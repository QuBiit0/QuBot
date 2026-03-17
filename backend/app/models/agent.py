"""
Agent models - AgentClass, Agent, AgentTool
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Index
from sqlmodel import Column, Field, Relationship, SQLModel

from .enums import AgentStatusEnum, DomainEnum, GenderEnum


class AgentClass(SQLModel, table=True):
    """Defines archetypes for agents — both predefined system classes and user-created custom classes"""

    __tablename__ = "agent_class"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: str = Field(max_length=500)
    domain: DomainEnum = Field(index=True)
    is_custom: bool = Field(default=False)
    # JSON: {sprite_id, color_primary, color_secondary, icon, badge}
    default_avatar_config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agents: list["Agent"] = Relationship(back_populates="agent_class")

    __table_args__ = (
        Index("idx_agent_class_domain", "domain"),
        Index("idx_agent_class_name", "name"),
    )


class Agent(SQLModel, table=True):
    """Individual AI agent instances with role, personality, LLM config, and avatar"""

    __tablename__ = "agent"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    gender: GenderEnum
    class_id: UUID = Field(foreign_key="agent_class.id", index=True)
    domain: DomainEnum = Field(index=True)
    role_description: str = Field(max_length=500)
    # JSON: {detail_oriented: 0-100, risk_tolerance: 0-100, formality: 0-100,
    #        strengths: [str], weaknesses: [str], communication_style: str}
    personality: dict = Field(default_factory=dict, sa_column=Column(JSON))
    llm_config_id: UUID = Field(foreign_key="llm_config.id")
    # JSON: {sprite_id, color_primary, color_secondary, icon, desk_position: {x, y}}
    avatar_config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    status: AgentStatusEnum = Field(default=AgentStatusEnum.IDLE, index=True)
    current_task_id: UUID | None = Field(default=None, foreign_key="task.id")
    is_orchestrator: bool = Field(default=False)
    last_active_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agent_class: AgentClass | None = Relationship(back_populates="agents")
    current_task: Optional["Task"] = Relationship(
        back_populates="assigned_agent",
        sa_relationship_kwargs={"foreign_keys": "Agent.current_task_id"},
    )
    tasks: list["Task"] = Relationship(
        back_populates="assigned_agent",
        sa_relationship_kwargs={"foreign_keys": "Task.assigned_agent_id"},
    )
    tools: list["AgentTool"] = Relationship(back_populates="agent")
    memories: list["AgentMemory"] = Relationship(back_populates="agent")
    llm_config: Optional["LlmConfig"] = Relationship(back_populates="agents")
    __table_args__ = (
        Index("idx_agent_status", "status"),
        Index("idx_agent_domain", "domain"),
    )


class AgentTool(SQLModel, table=True):
    """Many-to-many association between agents and tools with permission levels"""

    __tablename__ = "agent_tool"

    agent_id: UUID = Field(foreign_key="agent.id", primary_key=True)
    tool_id: UUID = Field(foreign_key="tool.id", primary_key=True)
    permissions: str = Field(default="READ_ONLY")  # PermissionEnum value
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agent: Agent | None = Relationship(back_populates="tools")
    tool: Optional["Tool"] = Relationship(back_populates="agent_assignments")
