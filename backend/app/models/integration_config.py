"""
IntegrationConfig - Stores per-tool configuration from the UI.
Allows each tool's credentials and settings to be managed without restarting.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class IntegrationConfig(SQLModel, table=True):
    __tablename__ = "integration_config"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tool_name: str = Field(unique=True, index=True, max_length=100)
    enabled: bool = Field(default=True)
    # Stores all config key/values; password fields are stored as-is
    # (encrypt with Fernet in production via a migration)
    config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
