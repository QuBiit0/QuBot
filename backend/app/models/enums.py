"""
Qubot Enums
All application enums in one place for consistency
"""

import enum


class DomainEnum(str, enum.Enum):
    """Agent/task domain classification"""

    TECH = "TECH"
    BUSINESS = "BUSINESS"
    FINANCE = "FINANCE"
    HR = "HR"
    MARKETING = "MARKETING"
    LEGAL = "LEGAL"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"


class GenderEnum(str, enum.Enum):
    """Agent gender options"""

    MALE = "MALE"
    FEMALE = "FEMALE"
    NON_BINARY = "NON_BINARY"


class AgentStatusEnum(str, enum.Enum):
    """Agent operational status"""

    IDLE = "IDLE"
    WORKING = "WORKING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"


class TaskStatusEnum(str, enum.Enum):
    """Task lifecycle status"""

    BACKLOG = "BACKLOG"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    FAILED = "FAILED"


class PriorityEnum(str, enum.Enum):
    """Task priority levels"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolTypeEnum(str, enum.Enum):
    """Tool/skill types"""

    SYSTEM_SHELL = "SYSTEM_SHELL"
    WEB_BROWSER = "WEB_BROWSER"
    FILESYSTEM = "FILESYSTEM"
    HTTP_API = "HTTP_API"
    SCHEDULER = "SCHEDULER"
    CUSTOM = "CUSTOM"


class LlmProviderEnum(str, enum.Enum):
    """LLM provider options"""

    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GOOGLE = "GOOGLE"
    GROQ = "GROQ"
    OPENROUTER = "OPENROUTER"
    DEEPSEEK = "DEEPSEEK"
    KIMI = "KIMI"
    MINIMAX = "MINIMAX"
    ZHIPU = "ZHIPU"
    LOCAL = "LOCAL"
    CUSTOM = "CUSTOM"
    OTHER = "OTHER"


class PermissionEnum(str, enum.Enum):
    """Tool permission levels"""

    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    DANGEROUS = "DANGEROUS"


class TaskEventTypeEnum(str, enum.Enum):
    """Task event types for audit log"""

    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    STARTED = "STARTED"
    TOOL_CALL = "TOOL_CALL"
    PROGRESS_UPDATE = "PROGRESS_UPDATE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMMENT = "COMMENT"


class MessagingPlatformEnum(str, enum.Enum):
    """Messaging platform types"""

    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    SLACK = "slack"


class MessageDirectionEnum(str, enum.Enum):
    """Message direction"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MemoryScopeEnum(str, enum.Enum):
    """Memory scope (for backwards compatibility)"""

    GLOBAL = "global"
    AGENT = "agent"
    TASK = "task"
