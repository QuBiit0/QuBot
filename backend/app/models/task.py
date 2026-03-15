"""
Task models - Task, TaskEvent
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import JSON, Index, String
from .enums import TaskStatusEnum, PriorityEnum, DomainEnum, TaskEventTypeEnum


class Task(SQLModel, table=True):
    """Work items managed on the Kanban board. Can have subtasks via parent_task_id"""
    __tablename__ = "task"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=200, index=True)
    description: str = Field(max_length=5000)
    status: TaskStatusEnum = Field(default=TaskStatusEnum.BACKLOG, index=True)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, index=True)
    domain_hint: Optional[DomainEnum] = Field(default=None, index=True)
    created_by: str = Field(max_length=100, default="user")  # "user" | "orchestrator" | "system"
    assigned_agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id", index=True)
    parent_task_id: Optional[UUID] = Field(default=None, foreign_key="task.id")
    scheduled_for: Optional[datetime] = Field(default=None)  # for SchedulerTool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    assigned_agent: Optional["Agent"] = Relationship(
        back_populates="tasks",
        sa_relationship_kwargs={"foreign_keys": "Task.assigned_agent_id"}
    )
    parent_task: Optional["Task"] = Relationship(
        back_populates="subtasks",
        sa_relationship_kwargs={"remote_side": "Task.id"}
    )
    subtasks: List["Task"] = Relationship(
        back_populates="parent_task",
        sa_relationship_kwargs={"foreign_keys": "Task.parent_task_id"}
    )
    events: List["TaskEvent"] = Relationship(back_populates="task")
    memory: Optional["TaskMemory"] = Relationship(back_populates="task")
    
    __table_args__ = (
        Index("idx_task_status_agent", "status", "assigned_agent_id"),
        Index("idx_task_domain_status", "domain_hint", "status"),
    )


class TaskEvent(SQLModel, table=True):
    """Append-only audit log of everything that happens during a task's lifecycle"""
    __tablename__ = "task_event"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="task.id", index=True)
    type: TaskEventTypeEnum
    # Event-specific data:
    # CREATED: {title, description, priority}
    # ASSIGNED: {agent_id, agent_name}
    # TOOL_CALL: {tool_name, tool_type, input, output, duration_ms, success}
    # PROGRESS_UPDATE: {message, iteration}
    # COMPLETED: {summary}
    # FAILED: {reason, iteration}
    # COMMENT: {author, text}
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    task: Optional[Task] = Relationship(back_populates="events")
    agent: Optional["Agent"] = Relationship()
    
    __table_args__ = (
        Index("idx_task_event_task_time", "task_id", "created_at"),
    )
