"""initial migration

Revision ID: 001
Revises:
Create Date: 2026-03-14 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create tables without dependencies first

    # agent_class - no dependencies
    op.create_table(
        "agent_class",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column(
            "description", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False
        ),
        sa.Column(
            "domain",
            sa.Enum(
                "TECH",
                "BUSINESS",
                "FINANCE",
                "HR",
                "MARKETING",
                "LEGAL",
                "PERSONAL",
                "OTHER",
                name="domainenum",
            ),
            nullable=False,
        ),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
        sa.Column("default_avatar_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_agent_class_domain", "agent_class", ["domain"], unique=False)
    op.create_index("idx_agent_class_name", "agent_class", ["name"], unique=False)
    op.create_index(
        op.f("ix_agent_class_domain"), "agent_class", ["domain"], unique=False
    )
    op.create_index(op.f("ix_agent_class_name"), "agent_class", ["name"], unique=True)

    # global_memory - no dependencies
    op.create_table(
        "global_memory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "content_type", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False
        ),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "embedding_ref", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_global_memory_key"), "global_memory", ["key"], unique=True)

    # llm_config - no dependencies
    op.create_table(
        "llm_config",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column(
            "provider",
            sa.Enum(
                "OPENAI",
                "ANTHROPIC",
                "GOOGLE",
                "GROQ",
                "OPENROUTER",
                "DEEPSEEK",
                "KIMI",
                "MINIMAX",
                "ZHIPU",
                "LOCAL",
                "CUSTOM",
                "OTHER",
                name="llmproviderenum",
            ),
            nullable=False,
        ),
        sa.Column(
            "model_name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False
        ),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("top_p", sa.Float(), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "api_key_ref", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False
        ),
        sa.Column("extra_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_llm_config_provider"), "llm_config", ["provider"], unique=False
    )

    # tool - no dependencies
    op.create_table(
        "tool",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column(
            "description", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False
        ),
        sa.Column(
            "type",
            sa.Enum(
                "SYSTEM_SHELL",
                "WEB_BROWSER",
                "FILESYSTEM",
                "HTTP_API",
                "SCHEDULER",
                "CUSTOM",
                name="tooltypeenum",
            ),
            nullable=False,
        ),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_tool_type", "tool", ["type"], unique=False)
    op.create_index(op.f("ix_tool_name"), "tool", ["name"], unique=True)
    op.create_index(op.f("ix_tool_type"), "tool", ["type"], unique=False)

    # messaging_channel - no dependencies
    op.create_table(
        "messaging_channel",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "platform",
            sa.Enum(
                "TELEGRAM", "WHATSAPP", "DISCORD", "SLACK", name="messagingplatformenum"
            ),
            nullable=False,
        ),
        sa.Column(
            "external_id", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False
        ),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_messaging_channel_platform",
        "messaging_channel",
        ["platform"],
        unique=False,
    )

    # task - depends on itself (self-reference via parent_task_id)
    op.create_table(
        "task",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "title", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False
        ),
        sa.Column(
            "description", sqlmodel.sql.sqltypes.AutoString(length=5000), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum(
                "BACKLOG",
                "IN_PROGRESS",
                "IN_REVIEW",
                "DONE",
                "FAILED",
                name="taskstatusenum",
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="priorityenum"),
            nullable=False,
        ),
        sa.Column(
            "domain_hint",
            sa.Enum(
                "TECH",
                "BUSINESS",
                "FINANCE",
                "HR",
                "MARKETING",
                "LEGAL",
                "PERSONAL",
                "OTHER",
                name="domainenum",
            ),
            nullable=True,
        ),
        sa.Column(
            "created_by", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False
        ),
        sa.Column("assigned_agent_id", sa.Uuid(), nullable=True),
        sa.Column("parent_task_id", sa.Uuid(), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("estimated_effort", sa.Integer(), nullable=True),
        sa.Column("actual_effort", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_task_id"],
            ["task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_task_domain_status", "task", ["domain_hint", "status"], unique=False
    )
    op.create_index(
        "idx_task_status_agent", "task", ["status", "assigned_agent_id"], unique=False
    )
    op.create_index(
        op.f("ix_task_assigned_agent_id"), "task", ["assigned_agent_id"], unique=False
    )
    op.create_index(op.f("ix_task_domain_hint"), "task", ["domain_hint"], unique=False)
    op.create_index(op.f("ix_task_priority"), "task", ["priority"], unique=False)
    op.create_index(op.f("ix_task_status"), "task", ["status"], unique=False)
    op.create_index(op.f("ix_task_title"), "task", ["title"], unique=False)

    # agent - depends on agent_class, llm_config, task
    op.create_table(
        "agent",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column(
            "gender",
            sa.Enum("MALE", "FEMALE", "NON_BINARY", name="genderenum"),
            nullable=False,
        ),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column(
            "domain",
            sa.Enum(
                "TECH",
                "BUSINESS",
                "FINANCE",
                "HR",
                "MARKETING",
                "LEGAL",
                "PERSONAL",
                "OTHER",
                name="domainenum",
            ),
            nullable=False,
        ),
        sa.Column(
            "role_description",
            sqlmodel.sql.sqltypes.AutoString(length=500),
            nullable=False,
        ),
        sa.Column("personality", sa.JSON(), nullable=True),
        sa.Column("llm_config_id", sa.Uuid(), nullable=False),
        sa.Column("avatar_config", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("IDLE", "WORKING", "ERROR", "OFFLINE", name="agentstatusenum"),
            nullable=False,
        ),
        sa.Column("current_task_id", sa.Uuid(), nullable=True),
        sa.Column("is_orchestrator", sa.Boolean(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["class_id"],
            ["agent_class.id"],
        ),
        sa.ForeignKeyConstraint(
            ["current_task_id"],
            ["task.id"],
        ),
        sa.ForeignKeyConstraint(
            ["llm_config_id"],
            ["llm_config.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_agent_domain", "agent", ["domain"], unique=False)
    op.create_index("idx_agent_status", "agent", ["status"], unique=False)
    op.create_index(op.f("ix_agent_class_id"), "agent", ["class_id"], unique=False)
    op.create_index(op.f("ix_agent_domain"), "agent", ["domain"], unique=False)
    op.create_index(op.f("ix_agent_name"), "agent", ["name"], unique=False)
    op.create_index(op.f("ix_agent_status"), "agent", ["status"], unique=False)

    # Add foreign key to task for assigned_agent_id (now that agent exists)
    op.create_foreign_key(
        "fk_task_assigned_agent", "task", "agent", ["assigned_agent_id"], ["id"]
    )

    # agent_tool - depends on agent and tool
    op.create_table(
        "agent_tool",
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("tool_id", sa.Uuid(), nullable=False),
        sa.Column(
            "permission",
            sa.Enum("READ_ONLY", "READ_WRITE", "DANGEROUS", name="permissionenum"),
            nullable=False,
        ),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tool.id"],
        ),
        sa.PrimaryKeyConstraint("agent_id", "tool_id"),
    )

    # llm_call_log - depends on agent and task
    op.create_table(
        "llm_call_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("config_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("was_cached", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent.id"],
        ),
        sa.ForeignKeyConstraint(
            ["config_id"],
            ["llm_config.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_llm_log_agent_time",
        "llm_call_log",
        ["agent_id", "created_at"],
        unique=False,
    )
    op.create_index("idx_llm_log_task", "llm_call_log", ["task_id"], unique=False)
    op.create_index(
        op.f("ix_llm_call_log_agent_id"), "llm_call_log", ["agent_id"], unique=False
    )
    op.create_index(
        op.f("ix_llm_call_log_task_id"), "llm_call_log", ["task_id"], unique=False
    )

    # agent_memory - depends on agent
    op.create_table(
        "agent_memory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column(
            "embedding_ref", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_agent_memory_agent_importance",
        "agent_memory",
        ["agent_id", "importance"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_memory_agent_id"), "agent_memory", ["agent_id"], unique=False
    )

    # task_event - depends on task
    op.create_table(
        "task_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "CREATED",
                "ASSIGNED",
                "STARTED",
                "TOOL_CALL",
                "PROGRESS_UPDATE",
                "COMPLETED",
                "FAILED",
                "COMMENT",
                name="taskeventtypeenum",
            ),
            nullable=False,
        ),
        sa.Column("agent_id", sa.Uuid(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_task_event_task_time",
        "task_event",
        ["task_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_event_task_id"), "task_event", ["task_id"], unique=False
    )

    # task_memory - depends on task
    op.create_table(
        "task_memory",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "embedding_ref", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_memory_task_id"), "task_memory", ["task_id"], unique=False
    )

    # conversation - depends on messaging_channel
    op.create_table(
        "conversation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column(
            "external_user_id",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=False,
        ),
        sa.Column(
            "external_user_name",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=False,
        ),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["messaging_channel.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_conversation_channel_user",
        "conversation",
        ["channel_id", "external_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_channel_id"), "conversation", ["channel_id"], unique=False
    )

    # conversation_message - depends on conversation
    op.create_table(
        "conversation_message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("INBOUND", "OUTBOUND", name="messagedirectionenum"),
            nullable=False,
        ),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "message_type", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_conv_message_conv_time",
        "conversation_message",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_message_conversation_id"),
        "conversation_message",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop in reverse order
    op.drop_table("conversation_message")
    op.drop_table("conversation")
    op.drop_table("task_memory")
    op.drop_table("task_event")
    op.drop_table("agent_memory")
    op.drop_table("llm_call_log")
    op.drop_table("agent_tool")
    op.drop_table("agent")
    op.drop_table("task")
    op.drop_table("messaging_channel")
    op.drop_table("tool")
    op.drop_table("llm_config")
    op.drop_table("global_memory")
    op.drop_table("agent_class")
