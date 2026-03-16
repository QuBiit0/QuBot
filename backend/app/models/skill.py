"""
Skill System Models

Inspired by OpenClaw's skills system but with enhanced security and visual management.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base


class SkillLanguage(str, Enum):
    """Supported languages for skill code."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"


class SkillParameter(Base):
    """Parameter definition for a skill."""

    __tablename__ = "skill_parameters"

    id = Column(String, primary_key=True)
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    param_type = Column(
        String(50), nullable=False
    )  # string, number, boolean, array, object
    description = Column(Text)
    required = Column(Boolean, default=True)
    default_value = Column(JSON)

    skill = relationship("Skill", back_populates="parameters")


class Skill(Base):
    """
    A skill is a reusable tool that agents can use.
    Similar to OpenClaw but with version control and permissions.
    """

    __tablename__ = "skills"

    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)  # Python or JS code
    language = Column(SQLEnum(SkillLanguage), default=SkillLanguage.PYTHON)

    # Metadata
    created_by = Column(String, ForeignKey("agents.id"))
    is_public = Column(Boolean, default=False)
    is_official = Column(Boolean, default=False)  # Qubot official skills
    version = Column(String(20), default="1.0.0")

    # Stats
    usage_count = Column(Integer, default=0)
    rating_average = Column(Integer, default=0)  # 1-5 stars
    rating_count = Column(Integer, default=0)

    # Relationships
    parameters = relationship(
        "SkillParameter", back_populates="skill", cascade="all, delete-orphan"
    )
    agent_skills = relationship(
        "AgentSkill", back_populates="skill", cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentSkill(Base):
    """
    Junction table: which skills are assigned to which agents.
    Includes agent-specific configuration.
    """

    __tablename__ = "agent_skills"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"))
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"))

    # Agent-specific configuration
    config = Column(JSON, default=dict)  # Parameter overrides
    is_enabled = Column(Boolean, default=True)
    permission_level = Column(
        String(20), default="READ_WRITE"
    )  # READ_ONLY, READ_WRITE, DANGEROUS

    # Usage tracking
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    # Relationships
    agent = relationship("Agent", back_populates="skills")
    skill = relationship("Skill", back_populates="agent_skills")

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Prevent duplicate assignments
        {"sqlite_autoincrement": True},
    )


class SkillExecutionLog(Base):
    """Audit log for skill executions."""

    __tablename__ = "skill_execution_logs"

    id = Column(String, primary_key=True)
    skill_id = Column(String, ForeignKey("skills.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    task_id = Column(String, ForeignKey("tasks.id"))

    # Execution details
    parameters = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    execution_time_ms = Column(Integer)

    # Status
    status = Column(String(20))  # success, error, timeout

    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic schemas for API
from typing import Literal

from pydantic import BaseModel, Field


class SkillParameterSchema(BaseModel):
    id: str | None = None
    name: str
    param_type: Literal["string", "number", "boolean", "array", "object"]
    description: str | None = None
    required: bool = True
    default_value: Any | None = None

    class Config:
        from_attributes = True


class SkillCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    code: str = Field(..., min_length=10)
    language: SkillLanguage = SkillLanguage.PYTHON
    is_public: bool = False
    parameters: list[SkillParameterSchema] = []


class SkillUpdateSchema(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    code: str | None = Field(None, min_length=10)
    is_public: bool | None = None
    parameters: list[SkillParameterSchema] | None = None


class SkillResponseSchema(BaseModel):
    id: str
    name: str
    description: str | None
    code: str | None = None  # Only return code if user has access
    language: SkillLanguage
    created_by: str | None
    is_public: bool
    is_official: bool
    version: str
    usage_count: int
    rating_average: int
    rating_count: int
    parameters: list[SkillParameterSchema]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentSkillAssignSchema(BaseModel):
    skill_id: str
    config: dict[str, Any] = {}
    permission_level: Literal["READ_ONLY", "READ_WRITE", "DANGEROUS"] = "READ_WRITE"


class AgentSkillResponseSchema(BaseModel):
    id: str
    agent_id: str
    skill_id: str
    skill_name: str
    skill_description: str | None
    is_enabled: bool
    permission_level: str
    use_count: int
    last_used_at: datetime | None
    config: dict[str, Any]

    class Config:
        from_attributes = True


class SkillExecuteSchema(BaseModel):
    parameters: dict[str, Any] = {}
    timeout: int = 30  # seconds


class SkillExecutionResponseSchema(BaseModel):
    success: bool
    result: Any | None = None
    error: str | None = None
    execution_time_ms: int
