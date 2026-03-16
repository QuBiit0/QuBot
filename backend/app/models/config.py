"""
Configuration models for dynamic settings stored in database
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Index, Text
from sqlmodel import JSON, Column, Field, SQLModel


class ConfigCategory(str, Enum):
    """Configuration categories"""

    GENERAL = "general"
    SECURITY = "security"
    LLM = "llm"
    MESSAGING = "messaging"
    INTEGRATIONS = "integrations"
    FEATURES = "features"
    UI = "ui"
    ADVANCED = "advanced"


class ConfigValueType(str, Enum):
    """Configuration value types"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    SECRET = "secret"  # Encrypted value


class SystemConfig(SQLModel, table=True):
    """
    Dynamic system configuration stored in database.
    Allows runtime configuration changes without restart.
    """

    __tablename__ = "system_config"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Key and category
    key: str = Field(max_length=100, index=True, unique=True)
    category: ConfigCategory = Field(default=ConfigCategory.GENERAL, index=True)

    # Value storage
    value_type: ConfigValueType = Field(default=ConfigValueType.STRING)
    value_string: str | None = Field(default=None, sa_column=Column(Text))
    value_integer: int | None = Field(default=None)
    value_float: float | None = Field(default=None)
    value_boolean: bool | None = Field(default=None)
    value_json: dict | None = Field(default=None, sa_column=Column(JSON))

    # Metadata
    description: str = Field(default="", max_length=500)
    is_editable: bool = Field(default=True)
    is_secret: bool = Field(default=False)  # If True, value is masked in API responses
    requires_restart: bool = Field(
        default=False
    )  # If True, requires app restart to take effect

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str | None = Field(default=None, max_length=100)

    __table_args__ = (Index("idx_config_category_key", "category", "key"),)

    def get_value(self) -> Any:
        """Get the configuration value based on type"""
        if self.value_type == ConfigValueType.STRING:
            return self.value_string
        elif self.value_type == ConfigValueType.INTEGER:
            return self.value_integer
        elif self.value_type == ConfigValueType.FLOAT:
            return self.value_float
        elif self.value_type == ConfigValueType.BOOLEAN:
            return self.value_boolean
        elif self.value_type == ConfigValueType.JSON:
            return self.value_json
        elif self.value_type == ConfigValueType.SECRET:
            return self.value_string  # Caller must handle encryption/decryption
        return None

    def set_value(self, value: Any, value_type: ConfigValueType | None = None):
        """Set the configuration value"""
        if value_type:
            self.value_type = value_type

        if self.value_type == ConfigValueType.STRING:
            self.value_string = str(value)
        elif self.value_type == ConfigValueType.INTEGER:
            self.value_integer = int(value)
        elif self.value_type == ConfigValueType.FLOAT:
            self.value_float = float(value)
        elif self.value_type == ConfigValueType.BOOLEAN:
            self.value_boolean = bool(value)
        elif self.value_type == ConfigValueType.JSON:
            self.value_json = value if isinstance(value, dict) else {"value": value}
        elif self.value_type == ConfigValueType.SECRET:
            self.value_string = str(value)


class ConfigPreset(SQLModel, table=True):
    """
    Configuration presets for quick switching between environments
    """

    __tablename__ = "config_preset"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    name: str = Field(max_length=100, unique=True)
    description: str = Field(default="", max_length=500)

    # Preset values (JSON object with key-value pairs)
    values: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Is this the active preset?
    is_active: bool = Field(default=False, index=True)

    # Category
    category: str = Field(
        default="custom", max_length=50
    )  # development, production, testing, custom

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConfigHistory(SQLModel, table=True):
    """
    Audit log of configuration changes
    """

    __tablename__ = "config_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    config_key: str = Field(max_length=100, index=True)
    category: str = Field(default="general", max_length=50)

    old_value: str | None = Field(default=None, sa_column=Column(Text))
    new_value: str | None = Field(default=None, sa_column=Column(Text))

    changed_by: str | None = Field(default=None, max_length=100)
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_reason: str | None = Field(default=None, max_length=500)

    __table_args__ = (Index("idx_config_history_key_time", "config_key", "changed_at"),)


class EnvironmentConfig(SQLModel, table=True):
    """
    Environment-specific overrides
    """

    __tablename__ = "environment_config"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    environment: str = Field(
        max_length=50, index=True
    )  # development, staging, production
    key: str = Field(max_length=100)
    value: dict = Field(sa_column=Column(JSON))

    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_env_config_env_key", "environment", "key", unique=True),
    )
