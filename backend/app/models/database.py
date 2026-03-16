from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship

from .enums import AgentStatusEnum, DomainEnum, MemoryScopeEnum, TaskStatusEnum

Base = declarative_base()


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    role = Column(String(100))
    skill = Column(String(100))
    domain = Column(SQLEnum(DomainEnum), default=DomainEnum.OTHER)
    status = Column(SQLEnum(AgentStatusEnum), default=AgentStatusEnum.OFFLINE)
    avatar_url = Column(String(255), nullable=True)
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="assigned_agent")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatusEnum), default=TaskStatusEnum.BACKLOG)
    priority = Column(Integer, default=0)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    assigned_agent = relationship("Agent", back_populates="tasks")
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(SQLEnum(MemoryScopeEnum), index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    content = Column(Text)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
