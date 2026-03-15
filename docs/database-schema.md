# Qubot — Database Schema

> **ORM**: SQLModel (SQLAlchemy 2.0 + Pydantic v2)
> **Database**: PostgreSQL 16
> **Migrations**: Alembic

---

## 1. Enums

All enums are defined in `backend/app/models/enums.py` and used as Python `enum.Enum` subclasses with PostgreSQL native enum types.

```python
# backend/app/models/enums.py
import enum

class DomainEnum(str, enum.Enum):
    TECH = "TECH"
    BUSINESS = "BUSINESS"
    FINANCE = "FINANCE"
    HR = "HR"
    MARKETING = "MARKETING"
    LEGAL = "LEGAL"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"

class GenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    NON_BINARY = "NON_BINARY"

class AgentStatusEnum(str, enum.Enum):
    IDLE = "IDLE"
    WORKING = "WORKING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"

class TaskStatusEnum(str, enum.Enum):
    BACKLOG = "BACKLOG"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    FAILED = "FAILED"

class PriorityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ToolTypeEnum(str, enum.Enum):
    SYSTEM_SHELL = "SYSTEM_SHELL"
    WEB_BROWSER = "WEB_BROWSER"
    FILESYSTEM = "FILESYSTEM"
    HTTP_API = "HTTP_API"
    SCHEDULER = "SCHEDULER"
    CUSTOM = "CUSTOM"

class LlmProviderEnum(str, enum.Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GOOGLE = "GOOGLE"
    GROQ = "GROQ"
    LOCAL = "LOCAL"
    OTHER = "OTHER"

class PermissionEnum(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    DANGEROUS = "DANGEROUS"

class TaskEventTypeEnum(str, enum.Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    STARTED = "STARTED"
    TOOL_CALL = "TOOL_CALL"
    PROGRESS_UPDATE = "PROGRESS_UPDATE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMMENT = "COMMENT"

class MessagingPlatformEnum(str, enum.Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    SLACK = "slack"

class MessageDirectionEnum(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
```

---

## 2. Table: `AgentClass`

**Purpose**: Defines archetypes for agents — both predefined system classes and user-created custom classes.

```python
# backend/app/models/agent.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Index
from .enums import DomainEnum

class AgentClass(SQLModel, table=True):
    __tablename__ = "agent_class"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: str = Field(max_length=500)
    domain: DomainEnum = Field(index=True)
    is_custom: bool = Field(default=False)
    # JSON: {sprite_id, color_primary, color_secondary, icon, badge}
    default_avatar_config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**SQL DDL equivalent:**
```sql
CREATE TABLE agent_class (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500) NOT NULL,
    domain      agent_domain_enum NOT NULL,
    is_custom   BOOLEAN NOT NULL DEFAULT FALSE,
    default_avatar_config JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),

    INDEX idx_agent_class_domain (domain),
    INDEX idx_agent_class_name (name)
);
```

### Seed Data (17 Predefined Classes)

```python
# backend/app/seeds/agent_classes.py
PREDEFINED_CLASSES = [
    # TECH Domain
    {
        "name": "Ethical Hacker",
        "description": "Security specialist focused on finding vulnerabilities and hardening systems",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "hacker", "color_primary": "#00FF41", "color_secondary": "#1a1a1a", "icon": "🔐", "badge": "SEC"}
    },
    {
        "name": "Systems Architect",
        "description": "Designs and oversees complex software architectures and infrastructure",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "architect", "color_primary": "#4A90E2", "color_secondary": "#1a2744", "icon": "🏗️", "badge": "ARCH"}
    },
    {
        "name": "Backend Developer",
        "description": "Builds APIs, services, databases, and server-side logic",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "backend_dev", "color_primary": "#7B2FBE", "color_secondary": "#2d1a44", "icon": "⚙️", "badge": "BE"}
    },
    {
        "name": "Frontend Developer",
        "description": "Creates user interfaces and interactive web applications",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "frontend_dev", "color_primary": "#F59E0B", "color_secondary": "#44300a", "icon": "🎨", "badge": "FE"}
    },
    {
        "name": "DevOps Engineer",
        "description": "Manages CI/CD pipelines, infrastructure, deployments and reliability",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "devops", "color_primary": "#10B981", "color_secondary": "#0a3327", "icon": "🚀", "badge": "OPS"}
    },
    {
        "name": "Data Scientist",
        "description": "Analyzes data, builds models, and extracts insights from large datasets",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "data_scientist", "color_primary": "#EF4444", "color_secondary": "#440a0a", "icon": "📊", "badge": "DS"}
    },
    {
        "name": "ML Engineer",
        "description": "Designs, trains, and deploys machine learning models and pipelines",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "ml_engineer", "color_primary": "#8B5CF6", "color_secondary": "#2a1a44", "icon": "🧠", "badge": "ML"}
    },
    {
        "name": "Data Analyst",
        "description": "Transforms raw data into actionable business insights and reports",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "data_analyst", "color_primary": "#06B6D4", "color_secondary": "#0a2a30", "icon": "📈", "badge": "DA"}
    },
    {
        "name": "QA Engineer",
        "description": "Designs and executes test strategies to ensure software quality",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "qa", "color_primary": "#84CC16", "color_secondary": "#1a2a06", "icon": "✅", "badge": "QA"}
    },
    {
        "name": "AI Researcher",
        "description": "Researches AI capabilities, prompt engineering, and LLM optimization",
        "domain": "TECH",
        "default_avatar_config": {"sprite_id": "ai_researcher", "color_primary": "#F97316", "color_secondary": "#44200a", "icon": "🔬", "badge": "AI"}
    },
    # FINANCE Domain
    {
        "name": "Finance Manager",
        "description": "Oversees financial operations, budgeting, and strategic financial decisions",
        "domain": "FINANCE",
        "default_avatar_config": {"sprite_id": "finance_manager", "color_primary": "#D97706", "color_secondary": "#44260a", "icon": "💰", "badge": "FIN"}
    },
    {
        "name": "Financial Analyst",
        "description": "Analyzes financial data, models, and provides investment recommendations",
        "domain": "FINANCE",
        "default_avatar_config": {"sprite_id": "fin_analyst", "color_primary": "#B45309", "color_secondary": "#3a1a06", "icon": "📉", "badge": "FA"}
    },
    # BUSINESS Domain
    {
        "name": "Product Manager",
        "description": "Defines product strategy, roadmaps, and coordinates cross-functional teams",
        "domain": "BUSINESS",
        "default_avatar_config": {"sprite_id": "pm", "color_primary": "#0EA5E9", "color_secondary": "#0a2a38", "icon": "📋", "badge": "PM"}
    },
    {
        "name": "Operations Manager",
        "description": "Optimizes business processes, logistics, and operational efficiency",
        "domain": "BUSINESS",
        "default_avatar_config": {"sprite_id": "ops_manager", "color_primary": "#64748B", "color_secondary": "#1a2030", "icon": "⚡", "badge": "OPS"}
    },
    # HR Domain
    {
        "name": "HR Manager",
        "description": "Manages recruitment, employee relations, and organizational culture",
        "domain": "HR",
        "default_avatar_config": {"sprite_id": "hr_manager", "color_primary": "#EC4899", "color_secondary": "#44102a", "icon": "👥", "badge": "HR"}
    },
    # MARKETING Domain
    {
        "name": "Digital Marketing Specialist",
        "description": "Plans and executes digital marketing campaigns, SEO, and growth strategies",
        "domain": "MARKETING",
        "default_avatar_config": {"sprite_id": "marketer", "color_primary": "#F43F5E", "color_secondary": "#44101a", "icon": "📣", "badge": "MKT"}
    },
    # LEGAL Domain
    {
        "name": "Legal Counsel",
        "description": "Provides legal guidance, contract review, and compliance advice",
        "domain": "LEGAL",
        "default_avatar_config": {"sprite_id": "legal", "color_primary": "#1E293B", "color_secondary": "#0a1020", "icon": "⚖️", "badge": "LEG"}
    },
]
```

---

## 3. Table: `LlmConfig`

**Purpose**: Stores LLM provider configurations. Each agent references one config.

```python
class LlmConfig(SQLModel, table=True):
    __tablename__ = "llm_config"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100)                        # Display name, e.g. "GPT-4o Production"
    provider: LlmProviderEnum = Field(index=True)
    model_name: str = Field(max_length=100)                  # e.g. "gpt-4o", "claude-3-5-sonnet-20241022"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    # Stores the ENV VAR NAME (e.g. "OPENAI_API_KEY"), NEVER the key value
    api_key_ref: str = Field(max_length=100)
    # JSON: extra provider-specific params (e.g. {"base_url": "http://localhost:11434"} for Ollama)
    extra_config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**SQL DDL equivalent:**
```sql
CREATE TABLE llm_config (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    provider    llm_provider_enum NOT NULL,
    model_name  VARCHAR(100) NOT NULL,
    temperature FLOAT NOT NULL DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),
    top_p       FLOAT NOT NULL DEFAULT 1.0 CHECK (top_p >= 0 AND top_p <= 1),
    max_tokens  INTEGER NOT NULL DEFAULT 4096 CHECK (max_tokens >= 1),
    api_key_ref VARCHAR(100) NOT NULL,
    extra_config JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 4. Table: `Tool`

**Purpose**: Registry of available tools/skills that agents can use.

```python
class Tool(SQLModel, table=True):
    __tablename__ = "tool"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    type: ToolTypeEnum = Field(index=True)
    description: str = Field(max_length=1000)   # Used verbatim in LLM prompts
    # JSON Schema (OpenAI function_call compatible)
    input_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    output_schema: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Type-specific config: HTTP base_url/auth, Shell allowed_cmds, etc.
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    is_dangerous: bool = Field(default=False)   # Requires DANGEROUS permission to use
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Config examples per type:**
```json
// HTTP_API
{
  "base_url": "https://api.example.com",
  "default_headers": {"Content-Type": "application/json"},
  "auth_type": "bearer",
  "auth_env_ref": "EXAMPLE_API_KEY",
  "timeout": 30,
  "allowed_domains": ["api.example.com"]
}

// SYSTEM_SHELL
{
  "allowed_commands": ["ls", "cat", "grep", "find", "python3", "node"],
  "working_directory": "/workspace",
  "timeout_seconds": 30,
  "env_passthrough": []
}

// WEB_BROWSER
{
  "timeout": 15,
  "user_agent": "Qubot/1.0",
  "max_content_length": 50000
}

// FILESYSTEM
{
  "base_directory": "/workspace/files",
  "allowed_extensions": [".txt", ".md", ".json", ".csv", ".py", ".js"],
  "max_file_size_bytes": 1048576
}

// SCHEDULER
{
  "max_delay_seconds": 86400
}
```

---

## 5. Table: `Agent`

**Purpose**: Individual AI agent instances with role, personality, LLM config, and avatar.

```python
class Agent(SQLModel, table=True):
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
    current_task_id: Optional[UUID] = Field(default=None, foreign_key="task.id")
    is_orchestrator: bool = Field(default=False)
    last_active_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Personality JSON example:**
```json
{
  "detail_oriented": 80,
  "risk_tolerance": 30,
  "formality": 70,
  "strengths": ["financial modeling", "data analysis", "risk assessment"],
  "weaknesses": ["creative tasks", "ambiguous requirements"],
  "communication_style": "formal and precise, prefers structured outputs"
}
```

**Avatar Config JSON example:**
```json
{
  "sprite_id": "finance_manager",
  "color_primary": "#D97706",
  "color_secondary": "#44260a",
  "icon": "💰",
  "desk_position": {"x": 3, "y": 1}
}
```

---

## 6. Table: `AgentTool` (Many-to-Many)

**Purpose**: Associates agents with tools and defines permission levels.

```python
class AgentTool(SQLModel, table=True):
    __tablename__ = "agent_tool"

    agent_id: UUID = Field(foreign_key="agent.id", primary_key=True)
    tool_id: UUID = Field(foreign_key="tool.id", primary_key=True)
    permissions: PermissionEnum = Field(default=PermissionEnum.READ_ONLY)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 7. Table: `Task`

**Purpose**: Work items managed on the Kanban board. Can have subtasks via `parent_task_id`.

```python
class Task(SQLModel, table=True):
    __tablename__ = "task"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=200, index=True)
    description: str = Field(max_length=5000)
    status: TaskStatusEnum = Field(default=TaskStatusEnum.BACKLOG, index=True)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, index=True)
    domain_hint: Optional[DomainEnum] = Field(default=None, index=True)
    created_by: str = Field(max_length=100, default="user")  # "user" | "orchestrator" | "system"
    assigned_agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id", index=True)
    parent_task_id: Optional[UUID] = Field(default=None, foreign_key="task.id")  # subtasks
    scheduled_for: Optional[datetime] = Field(default=None)  # for SchedulerTool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    __table_args__ = (
        Index("idx_task_status_agent", "status", "assigned_agent_id"),
        Index("idx_task_domain_status", "domain_hint", "status"),
    )
```

---

## 8. Table: `TaskEvent`

**Purpose**: Append-only audit log of everything that happens during a task's lifecycle. Never updated, only inserted.

```python
class TaskEvent(SQLModel, table=True):
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

    __table_args__ = (
        Index("idx_task_event_task_time", "task_id", "created_at"),
    )
```

---

## 9. Table: `GlobalMemory`

**Purpose**: Shared knowledge base available to all agents. Key-value store with tagging.

```python
class GlobalMemory(SQLModel, table=True):
    __tablename__ = "global_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: str = Field(max_length=200, unique=True, index=True)
    content: str                                              # Can be markdown, text, or JSON string
    content_type: str = Field(max_length=20, default="text") # "text" | "markdown" | "json"
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    # Future vector DB chunk ID (leave null until vector DB integrated)
    embedding_ref: Optional[str] = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 10. Table: `AgentMemory`

**Purpose**: Per-agent memory. Agents write observations here; retrieved in context window.

```python
class AgentMemory(SQLModel, table=True):
    __tablename__ = "agent_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID = Field(foreign_key="agent.id", index=True)
    key: str = Field(max_length=200)
    content: str
    importance: int = Field(default=3, ge=1, le=5)  # 1=low, 5=critical
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_agent_memory_agent_importance", "agent_id", "importance"),
    )
```

---

## 11. Table: `TaskMemory`

**Purpose**: LLM-generated summary of a completed task. Used for future context injection.

```python
class TaskMemory(SQLModel, table=True):
    __tablename__ = "task_memory"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="task.id", unique=True, index=True)
    summary: str                           # LLM-generated summary of what was accomplished
    key_facts: list[str] = Field(default_factory=list, sa_column=Column(JSON))  # Bullet points
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 12. Table: `LlmCallLog` (Observability)

**Purpose**: Logs every LLM API call for cost tracking and debugging.

```python
class LlmCallLog(SQLModel, table=True):
    __tablename__ = "llm_call_log"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id", index=True)
    task_id: Optional[UUID] = Field(default=None, foreign_key="task.id", index=True)
    provider: LlmProviderEnum
    model_name: str = Field(max_length=100)
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    finish_reason: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_llm_log_agent_time", "agent_id", "created_at"),
        Index("idx_llm_log_task", "task_id"),
    )
```

---

## 13. Table: `MessagingChannel`

**Purpose**: Stores one record per connected messaging platform bot/app. Credentials are stored as env var name references.

```python
# backend/app/models/messaging.py
class MessagingChannel(SQLModel, table=True):
    __tablename__ = "messaging_channel"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    platform: MessagingPlatformEnum
    name: str = Field(max_length=100)       # Human label, e.g. "Main Telegram Bot"
    is_active: bool = Field(default=True)

    # JSON with env var name references — NEVER actual tokens
    # Telegram: {"bot_token_ref": "TELEGRAM_BOT_TOKEN", "secret_token_ref": "..."}
    # WhatsApp: {"phone_number_id_ref": "...", "access_token_ref": "...", ...}
    # Discord:  {"bot_token_ref": "...", "public_key_ref": "..."}
    # Slack:    {"bot_token_ref": "...", "signing_secret_ref": "..."}
    config: dict = Field(sa_column=Column(JSONB), default={})

    # Optional: route all messages from this channel to a specific agent
    # If null, uses the global orchestrator agent
    assigned_agent_id: Optional[UUID] = Field(default=None, foreign_key="agent.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_messaging_channel_platform", "platform"),
    )
```

## 14. Table: `Conversation`

**Purpose**: One record per (channel × external user). Tracks conversation identity and rolling history.

```python
class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    channel_id: UUID = Field(foreign_key="messaging_channel.id", index=True)

    external_user_id: str = Field(max_length=200)   # Platform user ID / phone number
    external_chat_id: str = Field(max_length=200)   # Platform chat/channel ID

    # Last N messages kept as context for the orchestrator
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    history: list[dict] = Field(sa_column=Column(JSONB), default=[])

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_conversation_channel_user", "channel_id", "external_user_id"),
    )
```

## 15. Table: `ConversationMessage`

**Purpose**: Append-only log of every inbound and outbound message across all messaging platforms.

```python
class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversation_message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", index=True)
    direction: MessageDirectionEnum         # INBOUND | OUTBOUND
    content: str                            # Plain text content
    platform_message_id: str = Field(max_length=200)   # Native platform message ID
    metadata: dict = Field(sa_column=Column(JSONB), default={})
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_conv_message_conv_time", "conversation_id", "created_at"),
    )
```

---

## 16. Entity Relationship Diagram

```
AgentClass ◄────────── Agent ──────────────► LlmConfig
    │                    │                       │
    │                    │ current_task_id        │
    │                    ▼                        │
    │             ┌─────Task◄────parent_task_id──┤
    │             │      │                        │
    │             │      ▼                        │
    │             │  TaskEvent                    │
    │             │      │                        │
    │             │      ▼                        │
    │             │  TaskMemory                   │
    │             │                               │
    │         AgentTool                      LlmCallLog
    │             │
    │           Tool
    │
AgentMemory ◄── Agent
GlobalMemory (standalone)

MessagingChannel ──────────────► Agent (assigned_agent_id, optional)
    │
    ▼
Conversation
    │
    ▼
ConversationMessage
```

**Relationships summary:**
- `Agent` → `AgentClass` (many-to-one)
- `Agent` → `LlmConfig` (many-to-one)
- `Agent` → `Task` (current_task, optional many-to-one)
- `Agent` ↔ `Tool` via `AgentTool` (many-to-many)
- `Task` → `Agent` (assigned_agent, optional many-to-one)
- `Task` → `Task` (parent_task, optional self-referential)
- `TaskEvent` → `Task` (many-to-one)
- `TaskEvent` → `Agent` (optional many-to-one)
- `TaskMemory` → `Task` (one-to-one)
- `AgentMemory` → `Agent` (many-to-one)
- `LlmCallLog` → `Agent` (optional many-to-one)
- `LlmCallLog` → `Task` (optional many-to-one)

---

## 14. Indexes Summary

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| `agent_class` | `idx_agent_class_domain` | `domain` | Filter by domain in wizard |
| `agent` | `idx_agent_status` | `status` | Filter active/idle agents |
| `agent` | `idx_agent_domain` | `domain` | Assignment algorithm |
| `task` | `idx_task_status_agent` | `status, assigned_agent_id` | Kanban queries |
| `task` | `idx_task_domain_status` | `domain_hint, status` | Agent assignment filter |
| `task_event` | `idx_task_event_task_time` | `task_id, created_at` | Timeline queries |
| `agent_memory` | `idx_agent_memory_agent_importance` | `agent_id, importance` | Context retrieval |
| `llm_call_log` | `idx_llm_log_agent_time` | `agent_id, created_at` | Cost reports |

---

## 15. Alembic Migration: `001_initial_schema.py`

```python
# backend/alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Create enums first
    op.execute("CREATE TYPE domain_enum AS ENUM ('TECH','BUSINESS','FINANCE','HR','MARKETING','LEGAL','PERSONAL','OTHER')")
    op.execute("CREATE TYPE gender_enum AS ENUM ('MALE','FEMALE','NON_BINARY')")
    op.execute("CREATE TYPE agent_status_enum AS ENUM ('IDLE','WORKING','ERROR','OFFLINE')")
    op.execute("CREATE TYPE task_status_enum AS ENUM ('BACKLOG','IN_PROGRESS','IN_REVIEW','DONE','FAILED')")
    op.execute("CREATE TYPE priority_enum AS ENUM ('LOW','MEDIUM','HIGH','CRITICAL')")
    op.execute("CREATE TYPE tool_type_enum AS ENUM ('SYSTEM_SHELL','WEB_BROWSER','FILESYSTEM','HTTP_API','SCHEDULER','CUSTOM')")
    op.execute("CREATE TYPE llm_provider_enum AS ENUM ('OPENAI','ANTHROPIC','GOOGLE','GROQ','LOCAL','OTHER')")
    op.execute("CREATE TYPE permission_enum AS ENUM ('READ_ONLY','READ_WRITE','DANGEROUS')")
    op.execute("CREATE TYPE task_event_type_enum AS ENUM ('CREATED','ASSIGNED','STARTED','TOOL_CALL','PROGRESS_UPDATE','COMPLETED','FAILED','COMMENT')")

    op.create_table("agent_class", ...)  # as per model above
    op.create_table("llm_config", ...)
    op.create_table("tool", ...)
    # agent references llm_config and agent_class
    op.create_table("agent", ...)
    op.create_table("agent_tool", ...)
    # task self-references (parent_task_id added separately to avoid circular)
    op.create_table("task", ...)
    op.create_table("task_event", ...)
    op.create_table("task_memory", ...)
    op.create_table("agent_memory", ...)
    op.create_table("global_memory", ...)
    op.create_table("llm_call_log", ...)

    # Add all indexes
    op.create_index("idx_agent_class_domain", "agent_class", ["domain"])
    op.create_index("idx_agent_status", "agent", ["status"])
    op.create_index("idx_agent_domain", "agent", ["domain"])
    op.create_index("idx_task_status_agent", "task", ["status", "assigned_agent_id"])
    op.create_index("idx_task_domain_status", "task", ["domain_hint", "status"])
    op.create_index("idx_task_event_task_time", "task_event", ["task_id", "created_at"])
    op.create_index("idx_agent_memory_agent_importance", "agent_memory", ["agent_id", "importance"])
    op.create_index("idx_llm_log_agent_time", "llm_call_log", ["agent_id", "created_at"])

def downgrade():
    op.drop_table("llm_call_log")
    op.drop_table("global_memory")
    op.drop_table("agent_memory")
    op.drop_table("task_memory")
    op.drop_table("task_event")
    op.drop_table("task")
    op.drop_table("agent_tool")
    op.drop_table("agent")
    op.drop_table("tool")
    op.drop_table("llm_config")
    op.drop_table("agent_class")
    # Drop enums
    op.execute("DROP TYPE IF EXISTS task_event_type_enum")
    # ... drop all enums
```

---

## 16. Database Configuration

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel
from .config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Detect stale connections
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```
