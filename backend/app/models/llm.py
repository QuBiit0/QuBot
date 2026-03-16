"""
LLM models - LlmConfig, LlmCallLog
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Index
from sqlmodel import Column, Field, Relationship, SQLModel

from .enums import LlmProviderEnum


class LlmConfig(SQLModel, table=True):
    """Stores LLM provider configurations. Each agent references one config"""

    __tablename__ = "llm_config"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100)  # Display name, e.g. "GPT-4o Production"
    provider: LlmProviderEnum = Field(index=True)
    model_name: str = Field(
        max_length=100
    )  # e.g. "gpt-4o", "claude-3-5-sonnet-20241022"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    # Stores the ENV VAR NAME (e.g. "OPENAI_API_KEY"), NEVER the key value
    api_key_ref: str = Field(max_length=100)
    # JSON: extra provider-specific params (e.g. {"base_url": "http://localhost:11434"} for Ollama)
    extra_config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agents: list["Agent"] = Relationship(back_populates="llm_config")
    call_logs: list["LlmCallLog"] = Relationship(back_populates="llm_config")


class LlmCallLog(SQLModel, table=True):
    """Logs every LLM API call for cost tracking and debugging"""

    __tablename__ = "llm_call_log"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_id: UUID | None = Field(default=None, foreign_key="agent.id", index=True)
    task_id: UUID | None = Field(default=None, foreign_key="task.id", index=True)
    llm_config_id: UUID | None = Field(default=None, foreign_key="llm_config.id")
    provider: LlmProviderEnum
    model_name: str = Field(max_length=100)
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    finish_reason: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    llm_config: LlmConfig | None = Relationship(back_populates="call_logs")

    __table_args__ = (
        Index("idx_llm_log_agent_time", "agent_id", "created_at"),
        Index("idx_llm_log_task", "task_id"),
    )
