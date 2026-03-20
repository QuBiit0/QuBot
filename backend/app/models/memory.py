"""
Memory models - GlobalMemory, AgentMemory, TaskMemory

Phase 3 additions:
- AgentMemory.embedding   : JSON — raw float list for Python cosine fallback
- AgentMemory.content_hash: str  — SHA-256 prefix for Phase 5 deduplication
- GlobalMemory.embedding  : JSON — same as above
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Index
from sqlmodel import Column, Field, Relationship, SQLModel


class GlobalMemory(SQLModel, table=True):
    """Shared knowledge base available to all agents."""

    __tablename__ = "global_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: str = Field(max_length=200, unique=True, index=True)
    content: str  # markdown, text, or JSON string
    content_type: str = Field(max_length=20, default="text")  # text | markdown | json
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Embedding stored as JSON float list (pgvector column added via migration 005)
    embedding: list[float] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    # Reference to pgvector row / external vector store chunk (optional)
    embedding_ref: str | None = Field(default=None, max_length=200)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMemory(SQLModel, table=True):
    """Per-agent memory. Agents write observations here; retrieved in context window."""

    __tablename__ = "agent_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agent.id", index=True)
    key: str = Field(max_length=200)
    content: str
    importance: int = Field(default=3, ge=1, le=5)  # 1=low, 5=critical

    # Embedding stored as JSON float list (pgvector column added via migration 005)
    embedding: list[float] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    # SHA-256 hex digest of content (first 64 chars) — used for deduplication
    content_hash: str | None = Field(default=None, max_length=64)

    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agent: Optional["Agent"] = Relationship(back_populates="memories")

    __table_args__ = (
        Index("idx_agent_memory_agent_importance", "agent_id", "importance"),
    )


class TaskMemory(SQLModel, table=True):
    """LLM-generated summary of a completed task. Created automatically after task completion."""

    __tablename__ = "task_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="task.id", unique=True, index=True)
    summary: str  # LLM-generated summary of what was accomplished
    key_facts: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    task: Optional["Task"] = Relationship(back_populates="memory")
