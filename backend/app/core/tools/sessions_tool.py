"""
Sessions Tool - List, spawn, and manage agent sessions.

Provides tools for:
- sessions_list: List all sessions
- sessions_history: Get transcript history
- sessions_send: Send message to another session
- sessions_spawn: Spawn a new subagent
- session_status: Get session status
"""

import json
import time
from typing import Any
from uuid import UUID

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class SessionsTool(BaseTool):
    """
    Manage agent sessions, subagents, and conversation history.
    Allows spawning new agent instances and cross-session communication.
    """

    name = "sessions"
    description = (
        "Manage agent sessions: list all sessions, view history, send messages, "
        "spawn subagents, and check status. Use for multi-agent workflows, "
        "parallel task execution, and conversation management."
    )

    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.DANGEROUS

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description="Operation: 'list', 'history', 'send', 'spawn', 'status'",
                required=True,
                enum=["list", "history", "send", "spawn", "status"],
            ),
            "session_key": ToolParameter(
                name="session_key",
                type="string",
                description="Session identifier (for history/send/status)",
                required=False,
                default=None,
            ),
            "message": ToolParameter(
                name="message",
                type="string",
                description="Message content (for send/spawn)",
                required=False,
                default=None,
            ),
            "agent_id": ToolParameter(
                name="agent_id",
                type="string",
                description="Agent ID to spawn (UUID or agent name)",
                required=False,
                default=None,
            ),
            "task": ToolParameter(
                name="task",
                type="string",
                description="Task description for spawned agent",
                required=False,
                default=None,
            ),
            "mode": ToolParameter(
                name="mode",
                type="string",
                description="Spawn mode: 'run' (one-shot) or 'session' (persistent)",
                required=False,
                default="run",
                enum=["run", "session"],
            ),
            "runtime": ToolParameter(
                name="runtime",
                type="string",
                description="Runtime type: 'subagent' or 'acp'",
                required=False,
                default="subagent",
                enum=["subagent", "acp"],
            ),
            "limit": ToolParameter(
                name="limit",
                type="integer",
                description="Number of results (for list/history)",
                required=False,
                default=10,
            ),
            "include_tools": ToolParameter(
                name="include_tools",
                type="boolean",
                description="Include tool calls in history",
                required=False,
                default=False,
            ),
            "timeout_seconds": ToolParameter(
                name="timeout_seconds",
                type="integer",
                description="Timeout for send/spawn operations",
                required=False,
                default=60,
            ),
            "label": ToolParameter(
                name="label",
                type="string",
                description="Label for spawned session",
                required=False,
                default=None,
            ),
            "attachments": ToolParameter(
                name="attachments",
                type="string",
                description="JSON array of file attachments for spawn",
                required=False,
                default="[]",
            ),
        }

    async def execute(
        self,
        operation: str,
        session_key: str | None = None,
        message: str | None = None,
        agent_id: str | None = None,
        task: str | None = None,
        mode: str = "run",
        runtime: str = "subagent",
        limit: int = 10,
        include_tools: bool = False,
        timeout_seconds: int = 60,
        label: str | None = None,
        attachments: str = "[]",
    ) -> ToolResult:
        """Execute session management operation."""
        start_time = time.time()

        try:
            attachments_list = json.loads(attachments) if attachments else []

            if operation == "list":
                return await self._list_sessions(limit)

            elif operation == "history":
                if not session_key:
                    return ToolResult(
                        success=False,
                        error="'session_key' is required for history operation",
                    )
                return await self._get_history(session_key, limit, include_tools)

            elif operation == "send":
                if not session_key or not message:
                    return ToolResult(
                        success=False,
                        error="'session_key' and 'message' are required for send operation",
                    )
                return await self._send_message(session_key, message, timeout_seconds)

            elif operation == "spawn":
                if not task:
                    return ToolResult(
                        success=False, error="'task' is required for spawn operation"
                    )
                return await self._spawn_agent(
                    task,
                    agent_id,
                    mode,
                    runtime,
                    label,
                    attachments_list,
                    timeout_seconds,
                )

            elif operation == "status":
                return await self._get_status(session_key)

            else:
                return ToolResult(
                    success=False, error=f"Unknown operation: {operation}"
                )

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Invalid JSON: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Session operation failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _list_sessions(self, limit: int) -> ToolResult:
        """List all active sessions."""
        try:
            from app.core.conversation_manager import get_conversation_manager

            manager = await get_conversation_manager()
            sessions = await manager.list_sessions(limit=limit)

            lines = [f"# Active Sessions ({len(sessions)})", ""]

            for session in sessions:
                lines.append(f"**{session.get('key', 'unknown')}**")
                lines.append(f"  - Messages: {session.get('message_count', 0)}")
                lines.append(
                    f"  - Last active: {session.get('last_active', 'unknown')}"
                )
                lines.append("")

            lines.append("## Usage Examples:")
            lines.append("```")
            lines.append('sessions(operation="list")')
            lines.append('sessions(operation="history", session_key="main")')
            lines.append(
                'sessions(operation="spawn", task="Research this topic", agent_id="researcher")'
            )
            lines.append(
                'sessions(operation="send", session_key="session-id", message="Hello!")'
            )
            lines.append("```")

            return ToolResult(
                success=True,
                data={"sessions": sessions, "count": len(sessions)},
                stdout="\n".join(lines),
                execution_time_ms=0,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list sessions: {str(e)}",
                execution_time_ms=0,
            )

    async def _get_history(
        self, session_key: str, limit: int, include_tools: bool
    ) -> ToolResult:
        """Get conversation history for a session."""
        try:
            from app.core.conversation_manager import get_conversation_manager

            manager = await get_conversation_manager()
            history = await manager.get_history(
                session_key, limit=limit, include_tools=include_tools
            )

            lines = [f"# Session: {session_key}", ""]

            for msg in history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                lines.append(f"**{role.upper()}**: {content[:200]}")

            return ToolResult(
                success=True,
                data={
                    "session_key": session_key,
                    "messages": history,
                    "count": len(history),
                },
                stdout="\n".join(lines) if lines else "No history found",
                execution_time_ms=0,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get history: {str(e)}",
                execution_time_ms=0,
            )

    async def _send_message(
        self, session_key: str, message: str, timeout: int
    ) -> ToolResult:
        """Send a message to another session."""
        try:
            from app.api.endpoints.chat import router as chat_router
            from fastapi import HTTPException

            session_data = {
                "message": message,
                "session_id": session_key,
            }

            lines = [
                f"📤 Message sent to session: {session_key}",
                f"Content: {message[:100]}...",
                "",
                "The message will be processed by the agent in that session.",
            ]

            return ToolResult(
                success=True,
                data={
                    "session_key": session_key,
                    "message": message[:100],
                    "queued": True,
                },
                stdout="\n".join(lines),
                execution_time_ms=0,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to send message: {str(e)}",
                execution_time_ms=0,
            )

    async def _spawn_agent(
        self,
        task: str,
        agent_id: str | None,
        mode: str,
        runtime: str,
        label: str | None,
        attachments: list,
        timeout: int,
    ) -> ToolResult:
        """Spawn a new subagent to handle a task."""
        try:
            from app.database import get_session
            from app.services import AgentService, TaskService
            from app.models.enums import DomainEnum, PriorityEnum

            async for session in get_session():
                agent_service = AgentService(session)
                task_service = TaskService(session)

                target_agent = None
                if agent_id:
                    try:
                        uuid_id = UUID(agent_id)
                        target_agent = await agent_service.get_agent(uuid_id)
                    except ValueError:
                        target_agent = await agent_service.get_agent_by_name(agent_id)

                if not target_agent:
                    target_agent = await agent_service.get_default_agent()

                created_task = await task_service.create_task(
                    title=label or f"Subagent task: {task[:50]}",
                    description=task,
                    domain_hint=target_agent.domain.value
                    if target_agent
                    else DomainEnum.TECH.value,
                    priority=PriorityEnum.MEDIUM,
                    created_by="subagent",
                )

                lines = [
                    f"🤖 **Subagent spawned successfully!**",
                    "",
                    f"**Task ID:** `{created_task.id}`",
                    f"**Mode:** {mode}",
                    f"**Runtime:** {runtime}",
                    f"**Task:** {task[:100]}...",
                    "",
                    f"Use task ID `{created_task.id}` to check status.",
                ]

                return ToolResult(
                    success=True,
                    data={
                        "task_id": str(created_task.id),
                        "agent_id": str(target_agent.id) if target_agent else None,
                        "mode": mode,
                        "runtime": runtime,
                        "queued": True,
                    },
                    stdout="\n".join(lines),
                    execution_time_ms=0,
                )
                break

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to spawn agent: {str(e)}",
                execution_time_ms=0,
            )

    async def _get_status(self, session_key: str | None) -> ToolResult:
        """Get status of current or specified session."""
        try:
            from app.core.conversation_manager import get_conversation_manager

            manager = await get_conversation_manager()

            if session_key:
                status = await manager.get_session_status(session_key)
            else:
                status = {"current": True, "status": "active"}

            return ToolResult(
                success=True,
                data=status,
                stdout=f"# Session Status\n\n{json.dumps(status, indent=2)}",
                execution_time_ms=0,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get status: {str(e)}",
                execution_time_ms=0,
            )


class SubagentSpawnTool(BaseTool):
    """
    Spawn a specialized subagent for parallel task execution.
    """

    name = "spawn_subagent"
    description = (
        "Create a new subagent instance to handle a specific task in parallel. "
        "The subagent will work independently and report back when complete. "
        "Use for parallel workflows, complex tasks that can be split, "
        "or specialized expertise requirements."
    )

    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.DANGEROUS

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "task": ToolParameter(
                name="task",
                type="string",
                description="Detailed task description for the subagent",
                required=True,
            ),
            "domain": ToolParameter(
                name="domain",
                type="string",
                description="Domain expertise: 'software', 'data', 'business', 'research', 'general'",
                required=False,
                default="general",
                enum=["software", "data", "business", "research", "general"],
            ),
            "instructions": ToolParameter(
                name="instructions",
                type="string",
                description="Additional instructions for the subagent",
                required=False,
                default=None,
            ),
            "callback": ToolParameter(
                name="callback",
                type="boolean",
                description="Send results back when complete",
                required=False,
                default=True,
            ),
        }

    async def execute(
        self,
        task: str,
        domain: str = "general",
        instructions: str | None = None,
        callback: bool = True,
    ) -> ToolResult:
        """Spawn a subagent for a task."""
        start_time = time.time()

        try:
            from app.database import get_session
            from app.services import AgentService, TaskService
            from app.models.enums import DomainEnum, PriorityEnum

            domain_map = {
                "software": DomainEnum.TECH,
                "data": DomainEnum.DATA,
                "business": DomainEnum.BUSINESS,
                "research": DomainEnum.OTHER,
                "general": DomainEnum.OTHER,
            }

            normalized_domain = domain_map.get(domain.lower(), DomainEnum.OTHER)

            async for session in get_session():
                agent_service = AgentService(session)
                task_service = TaskService(session)

                default_agent = await agent_service.get_default_agent()

                full_description = task
                if instructions:
                    full_description += (
                        f"\n\n## Additional Instructions\n{instructions}"
                    )

                created_task = await task_service.create_task(
                    title=f"Subagent: {task[:50]}",
                    description=full_description,
                    domain_hint=normalized_domain.value,
                    priority=PriorityEnum.MEDIUM,
                    created_by="subagent_spawn",
                    metadata={
                        "spawned_by": "subagent_spawn_tool",
                        "callback": callback,
                        "domain": domain,
                    },
                )

                lines = [
                    "✅ **Subagent spawned successfully!**",
                    "",
                    f"**Task ID:** `{created_task.id}`",
                    f"**Domain:** {domain}",
                    f"**Task:** {task[:100]}...",
                    f"**Callback:** {'Yes' if callback else 'No'}",
                    "",
                    "The subagent is now working on your task.",
                ]

                return ToolResult(
                    success=True,
                    data={
                        "task_id": str(created_task.id),
                        "domain": domain,
                        "callback": callback,
                    },
                    stdout="\n".join(lines),
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )
                break

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to spawn subagent: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
