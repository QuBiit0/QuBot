"""
MCPServer - Stores Model Context Protocol server configurations.
Agents can connect to external MCP servers to access additional tools.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class MCPServer(SQLModel, table=True):
    __tablename__ = "mcp_server"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=200)
    description: str = Field(default="", max_length=500)

    # Transport type: "sse" (HTTP/SSE), "stdio" (local process)
    server_type: str = Field(default="sse")

    # SSE/HTTP fields
    url: str = Field(default="")
    headers: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))

    # stdio fields
    command: str = Field(default="")
    args: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    env_vars: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))

    enabled: bool = Field(default=True)

    # Cached tool schemas from last sync
    tools_cache: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    last_connected: datetime | None = Field(default=None)

    # Connection status: "connected", "error", "disconnected"
    status: str = Field(default="disconnected")
    error_msg: str = Field(default="", max_length=1000)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
