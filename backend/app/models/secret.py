"""
Secret Model - Database model for encrypted secrets
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text, Index
from sqlmodel import SQLModel, Field


class Secret(SQLModel, table=True):
    """
    Database model for stored secrets.
    Values are encrypted at rest using Fernet encryption.
    """

    __tablename__ = "secrets"

    id: str = Field(primary_key=True, max_length=36)
    name: str = Field(max_length=255, index=True)
    category: str = Field(max_length=50, default="api_key")
    encrypted_value: str = Field(sa_column=Column(Text, nullable=False))
    description: Optional[str] = Field(default=None, max_length=500)
    user_id: Optional[str] = Field(default=None, max_length=36, index=True)
    created_by: Optional[str] = Field(default=None, max_length=36)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    tags: Optional[str] = Field(default=None, max_length=500)

    __table_args__ = (Index("ix_secrets_name_user", "name", "user_id", unique=True),)

    @property
    def tag_list(self) -> list[str]:
        """Parse tags from JSON string"""
        if not self.tags:
            return []
        import json

        try:
            return json.loads(self.tags)
        except Exception:
            return []

    @tag_list.setter
    def tag_list(self, value: list[str]):
        """Convert tags list to JSON string"""
        import json

        self.tags = json.dumps(value) if value else None
