"""
Workflow model - Visual workflow builder nodes/edges
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class Workflow(SQLModel, table=True):
    """Visual workflow definition (nodes + edges) built with ReactFlow."""

    __tablename__ = "workflow"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=200, index=True)
    description: str = Field(default="", max_length=2000)
    nodes: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    edges: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    is_active: bool = Field(default=True, index=True)
    created_by: str = Field(default="user", max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
