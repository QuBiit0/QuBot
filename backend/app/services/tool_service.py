"""
Tool Service - Business logic for tool management
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.enums import ToolTypeEnum
from ..models.tool import Tool


class ToolService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tool(
        self,
        name: str,
        tool_type: ToolTypeEnum,
        description: str,
        input_schema: dict,
        output_schema: dict,
        config: dict,
        is_dangerous: bool = False,
    ) -> Tool:
        """Create a new tool"""
        tool = Tool(
            name=name,
            type=tool_type,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            config=config,
            is_dangerous=is_dangerous,
        )
        self.session.add(tool)
        await self.session.commit()
        await self.session.refresh(tool)
        return tool

    async def get_tool(self, tool_id: UUID) -> Tool | None:
        """Get tool by ID"""
        result = await self.session.execute(select(Tool).where(Tool.id == tool_id))
        return result.scalar_one_or_none()

    async def get_tools(
        self,
        tool_type: ToolTypeEnum | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Tool]:
        """Get tools with optional filters"""
        query = select(Tool)

        if tool_type:
            query = query.where(Tool.type == tool_type)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_tool(self, tool_id: UUID, **updates) -> Tool | None:
        """Update tool fields"""
        tool = await self.get_tool(tool_id)
        if not tool:
            return None

        for key, value in updates.items():
            if hasattr(tool, key):
                setattr(tool, key, value)

        await self.session.commit()
        await self.session.refresh(tool)
        return tool

    async def delete_tool(self, tool_id: UUID) -> bool:
        """Delete a tool"""
        tool = await self.get_tool(tool_id)
        if not tool:
            return False

        await self.session.delete(tool)
        await self.session.commit()
        return True

    async def get_default_tools(self) -> list[Tool]:
        """Get or create default system tools"""
        result = await self.session.execute(select(Tool))
        tools = result.scalars().all()

        if not tools:
            # Create default tools
            default_tools = [
                {
                    "name": "Web Browser",
                    "tool_type": ToolTypeEnum.WEB_BROWSER,
                    "description": "Browse websites and extract information from web pages",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to browse"},
                            "extract_mode": {
                                "type": "string",
                                "enum": ["text", "links", "full"],
                            },
                        },
                        "required": ["url"],
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "links": {"type": "array"},
                        },
                    },
                    "config": {"timeout": 30, "max_content_length": 50000},
                    "is_dangerous": False,
                },
                {
                    "name": "HTTP API Client",
                    "tool_type": ToolTypeEnum.HTTP_API,
                    "description": "Make HTTP requests to external APIs and services",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "method": {
                                "type": "string",
                                "enum": ["GET", "POST", "PUT", "DELETE"],
                            },
                            "url": {"type": "string"},
                            "headers": {"type": "object"},
                            "body": {"type": "object"},
                        },
                        "required": ["method", "url"],
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "status_code": {"type": "integer"},
                            "body": {},
                        },
                    },
                    "config": {},
                    "is_dangerous": False,
                },
                {
                    "name": "File System",
                    "tool_type": ToolTypeEnum.FILESYSTEM,
                    "description": "Read and write files in a sandboxed environment",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["read", "write", "list"],
                            },
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["operation", "path"],
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "files": {"type": "array"},
                        },
                    },
                    "config": {"base_directory": "/workspace/files"},
                    "is_dangerous": False,
                },
                {
                    "name": "Shell Executor",
                    "tool_type": ToolTypeEnum.SYSTEM_SHELL,
                    "description": "Execute whitelisted shell commands",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "args": {"type": "array", "items": {"type": "string"}},
                            "timeout": {"type": "integer", "default": 60},
                        },
                        "required": ["command"],
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "stdout": {"type": "string"},
                            "stderr": {"type": "string"},
                            "returncode": {"type": "integer"},
                        },
                    },
                    "config": {
                        "allowed_commands": [
                            "ls",
                            "cat",
                            "grep",
                            "find",
                            "python3",
                            "node",
                        ],
                        "timeout_seconds": 60,
                    },
                    "is_dangerous": True,
                },
                {
                    "name": "Task Scheduler",
                    "tool_type": ToolTypeEnum.SCHEDULER,
                    "description": "Schedule future tasks and reminders",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "scheduled_for": {"type": "string", "format": "date-time"},
                        },
                        "required": ["title", "scheduled_for"],
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                        },
                    },
                    "config": {},
                    "is_dangerous": False,
                },
                {
                    "name": "Memory Write",
                    "tool_type": ToolTypeEnum.CUSTOM,
                    "description": "Store information in the agent's persistent memory",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "content": {"type": "string"},
                            "importance": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 5,
                            },
                        },
                        "required": ["key", "content"],
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "string"},
                        },
                    },
                    "config": {},
                    "is_dangerous": False,
                },
            ]

            for tool_data in default_tools:
                tool = Tool(**tool_data)
                self.session.add(tool)

            await self.session.commit()

            # Return fresh query
            result = await self.session.execute(select(Tool))
            return result.scalars().all()

        return tools
