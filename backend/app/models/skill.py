"""
Skill System Models (Híbrido)

Skills son directorios con SKILL.md + scripts ejecutables.
- Metadata en BD para queries rápidas
- Archivos en filesystem para portabilidad
- Scripts ejecutables para automatización

Estructura:
  skills/
  ├── skill-id/
  │   ├── SKILL.md          # Frontmatter + instrucciones
  │   ├── scripts/
  │   │   ├── run.py        # Script principal ejecutable
  │   │   └── utils.py       # Helpers
  │   ├── templates/
  │   ├── assets/
  │   └── references/
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


class SkillCategory(str, Enum):
    """Categorías para organizar skills."""

    DEVELOPMENT = "development"
    DATA = "data"
    DESIGN = "design"
    OPERATIONS = "operations"
    MARKETING = "marketing"
    RESEARCH = "research"
    CUSTOM = "custom"


class Skill(Base):
    """
    Skill metadata - la ruta al directorio está en filesystem.

    El archivo SKILL.md contiene frontmatter con toda la config
    pero repetimos ciertos campos en BD para queries rápidas.
    """

    __tablename__ = "skills"

    id = Column(String, primary_key=True)  # skill-id (kebab-case)

    # Metadata (también en SKILL.md frontmatter)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(SQLEnum(SkillCategory), default=SkillCategory.CUSTOM)
    icon = Column(String(50), default="📦")
    triggers = Column(JSON, default=list)

    # Filesystem path
    base_path = Column(String(500))

    # Ownership & visibility
    created_by = Column(String, ForeignKey("agents.id"))
    is_public = Column(Boolean, default=False)
    is_official = Column(Boolean, default=False)
    version = Column(String(20), default="1.0.0")

    # Stats
    usage_count = Column(Integer, default=0)
    rating_average = Column(Integer, default=0)
    rating_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent_skills = relationship(
        "AgentSkill", back_populates="skill", cascade="all, delete-orphan"
    )
    execution_logs = relationship(
        "SkillExecutionLog", back_populates="skill", cascade="all, delete-orphan"
    )


class AgentSkill(Base):
    """Skills asignados a agentes."""

    __tablename__ = "agent_skills"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"))
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"))

    config = Column(JSON, default=dict)
    is_enabled = Column(Boolean, default=True)
    permission_level = Column(String(20), default="READ")

    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    agent = relationship("Agent", back_populates="skills")
    skill = relationship("Skill", back_populates="agent_skills")

    created_at = Column(DateTime, default=datetime.utcnow)


class SkillExecutionLog(Base):
    """Log de ejecuciones de scripts dentro de skills."""

    __tablename__ = "skill_execution_logs"

    id = Column(String, primary_key=True)
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"))
    agent_id = Column(String, ForeignKey("agents.id"))
    task_id = Column(String, ForeignKey("tasks.id"))

    # Qué script se ejecutó
    script_path = Column(String(500))
    script_language = Column(String(20))  # python, javascript, bash

    # Input/Output
    parameters = Column(JSON)
    result = Column(JSON)
    output = Column(Text)  # stdout/stderr

    # Stats
    execution_time_ms = Column(Integer)
    status = Column(String(20))  # success, error, timeout
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    skill = relationship("Skill", back_populates="execution_logs")


# =============================================================================
# Pydantic Schemas
# =============================================================================

from typing import Literal
from pydantic import BaseModel, Field


class SkillCreateSchema(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: SkillCategory = SkillCategory.CUSTOM
    icon: str = "📦"
    triggers: list[str] = []
    is_public: bool = False


class SkillUpdateSchema(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    category: SkillCategory | None = None
    icon: str | None = None
    triggers: list[str] | None = None
    is_public: bool | None = None
    version: str | None = None


class SkillResponseSchema(BaseModel):
    id: str
    name: str
    description: str | None
    category: SkillCategory
    icon: str
    triggers: list[str]
    base_path: str | None
    created_by: str | None
    is_public: bool
    is_official: bool
    version: str
    usage_count: int
    rating_average: int
    rating_count: int
    has_scripts: bool = False
    has_templates: bool = False
    has_assets: bool = False
    has_references: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SkillContentSchema(BaseModel):
    """Contenido completo de un skill."""

    id: str
    name: str
    description: str | None
    category: SkillCategory
    icon: str
    triggers: list[str]
    version: str

    # Frontmatter original
    frontmatter: dict[str, Any]

    # Cuerpo del markdown
    content: str

    # Lista de archivos
    files: list[dict[str, str]]

    # Scripts disponibles
    scripts: list[str]


SkillContentResponse = SkillContentSchema


class SkillScriptSchema(BaseModel):
    """Script dentro de un skill."""

    name: str
    path: str
    language: str
    content: str | None = None  # None = solo metadata


class SkillExecuteSchema(BaseModel):
    """Ejecutar un script dentro de un skill."""

    script: str = "run.py"  # Script a ejecutar (default: run.py)
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout: int = 30  # segundos


class SkillExecutionResponseSchema(BaseModel):
    """Resultado de ejecutar un script."""

    success: bool
    script: str
    result: Any | None = None
    output: str | None = None
    execution_time_ms: int
    error: str | None = None


class AgentSkillAssignSchema(BaseModel):
    skill_id: str
    config: dict[str, Any] = {}
    permission_level: Literal["READ", "READ_WRITE"] = "READ"


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
