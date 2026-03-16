"""
Memory models - GlobalMemory, AgentMemory, TaskMemory
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Index
from sqlmodel import Column, Field, Relationship, SQLModel


class GlobalMemory(SQLModel, table=True):
    """Shared knowledge base available to all agents"""

    __tablename__ = "global_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: str = Field(max_length=200, unique=True, index=True)
    content: str  # Can be markdown, text, or JSON string
    content_type: str = Field(
        max_length=20, default="text"
    )  # "text" | "markdown" | "json"
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    # Future vector DB chunk ID (leave null until vector DB integrated)
    embedding_ref: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMemory(SQLModel, table=True):
    """Per-agent memory. Agents write observations here; retrieved in context window"""

    __tablename__ = "agent_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agent.id", index=True)
    key: str = Field(max_length=200)
    content: str
    importance: int = Field(default=3, ge=1, le=5)  # 1=low, 5=critical
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agent: Optional["Agent"] = Relationship(back_populates="memories")

    __table_args__ = (
        Index("idx_agent_memory_agent_importance", "agent_id", "importance"),
    )


class TaskMemory(SQLModel, table=True):
    """LLM-generated summary of a completed task. Created automatically after task completion"""

    __tablename__ = "task_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="task.id", unique=True, index=True)
    summary: str  # LLM-generated summary of what was accomplished
    key_facts: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    task: Optional["Task"] = Relationship(back_populates="memory")
