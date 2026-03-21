"""
Tool Execution Service - Execute tools and integrate with LLM providers

Includes:
- Built-in tool execution (ToolRegistry)
- MCP server tool routing (mcp__{server}__{tool} prefix)
- Enabled/disabled filter via IntegrationConfig
"""

import json
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..core.mcp_client import call_tool_http, call_tool_sse, call_tool_stdio
from ..core.providers import LlmResponse, ToolCall, ToolDefinition
from ..core.tools import ToolResult, get_tool_registry
from ..models.integration_config import IntegrationConfig
from ..models.mcp_server import MCPServer
from .llm_service import LLMService
from .task_service import TaskService


def _server_safe_name(name: str) -> str:
    """Convert server name to a safe snake_case identifier for tool prefixing."""
    return name.replace("-", "_").replace(" ", "_").replace(".", "_").lower()


class ToolExecutionService:
    """
    Service for executing tools and managing tool-LLM interactions.

    Handles:
    - Built-in tool execution with proper error handling
    - MCP server tool routing (prefix: mcp__{server}__{tool})
    - Filtering disabled tools via IntegrationConfig
    - Tool result formatting for LLM consumption
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tool_registry = get_tool_registry()

    # -------------------------------------------------------------------------
    # Tool Discovery
    # -------------------------------------------------------------------------

    async def get_tool_definitions_async(self) -> list[ToolDefinition]:
        """
        Get all tool definitions for the LLM:
          1. Built-in tools — filtered by IntegrationConfig.enabled
          2. MCP server tools — from all enabled MCPServer rows (via tools_cache)

        MCP tool names are prefixed: mcp__{server_safe_name}__{original_tool_name}
        """
        # 1. Disabled built-in tool names from DB
        disabled_result = await self.session.execute(
            select(IntegrationConfig).where(IntegrationConfig.enabled == False)  # noqa: E712
        )
        disabled_names: set[str] = {
            r.tool_name for r in disabled_result.scalars().all()
        }

        # 2. Built-in tools
        definitions: list[ToolDefinition] = []
        for tool_name in self.tool_registry.list_tools():
            if tool_name in disabled_names:
                continue
            tool = self.tool_registry.get(tool_name)
            if tool:
                schema = tool.get_schema()
                func = schema["function"]
                definitions.append(
                    ToolDefinition(
                        name=func["name"],
                        description=func["description"],
                        parameters=func["parameters"],
                    )
                )

        # 3. MCP server tools
        mcp_result = await self.session.execute(
            select(MCPServer).where(MCPServer.enabled == True)  # noqa: E712
        )
        servers = mcp_result.scalars().all()
        for server in servers:
            if not server.tools_cache:
                continue
            safe = _server_safe_name(server.name)
            for tool in server.tools_cache:
                tool_name = tool.get("name", "")
                if not tool_name:
                    continue
                raw_schema = tool.get("input_schema", {})
                # Ensure valid JSON Schema
                if isinstance(raw_schema, dict) and raw_schema.get("type") == "object":
                    parameters = raw_schema
                else:
                    parameters = {
                        "type": "object",
                        "properties": raw_schema
                        if isinstance(raw_schema, dict)
                        else {},
                    }
                definitions.append(
                    ToolDefinition(
                        name=f"mcp__{safe}__{tool_name}",
                        description=f"[MCP:{server.name}] {tool.get('description', '')}",
                        parameters=parameters,
                    )
                )

        return definitions

    def get_tool_definitions(self) -> list[ToolDefinition]:
        """
        Sync version — returns ONLY built-in tools (no MCP, no enabled filter).
        Kept for backward-compat with existing callers. Prefer get_tool_definitions_async().
        """
        definitions = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool:
                schema = tool.get_schema()
                func = schema["function"]
                definitions.append(
                    ToolDefinition(
                        name=func["name"],
                        description=func["description"],
                        parameters=func["parameters"],
                    )
                )
        return definitions

    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get all registered tools formatted for LLM (sync, built-in only)."""
        return self.tool_registry.get_tools_for_llm()

    # -------------------------------------------------------------------------
    # Tool Execution
    # -------------------------------------------------------------------------

    async def execute_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        agent_id: UUID | None = None,
        task_id: UUID | None = None,
    ) -> ToolResult:
        """Execute a built-in tool by name."""

        # Check tool profile permissions
        if agent_id:
            from app.main import get_tool_profile_service

            profile_service = get_tool_profile_service()
            if profile_service:
                config = profile_service.get_profile_config(agent_id)
                if config.deny_list and tool_name in config.deny_list:
                    return ToolResult(
                        success=False,
                        error=f"Tool '{tool_name}' is denied for this agent",
                    )
                if (
                    config.allow_list
                    and "*" not in config.allow_list
                    and tool_name not in config.allow_list
                ):
                    return ToolResult(
                        success=False,
                        error=f"Tool '{tool_name}' is not in agent's allowed tools",
                    )

        tool = self.tool_registry.get(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {tool_name}")

        is_valid, error = tool.validate_params(params)
        if not is_valid:
            return ToolResult(
                success=False, error=f"Parameter validation failed: {error}"
            )

        # Check for loops
        if agent_id:
            from app.main import get_loop_detection_service

            loop_service = get_loop_detection_service()
            if loop_service:
                loop_result = loop_service.analyze(agent_id)
                if loop_result and loop_result.is_loop:
                    return ToolResult(
                        success=False,
                        error=f"Loop detected: {loop_result.message}",
                        metadata={
                            "loop_type": loop_result.loop_type.value
                            if loop_result.loop_type
                            else None
                        },
                    )

        start_time = time.time()
        try:
            result = await tool.execute(**params)
        except Exception as e:
            result = ToolResult(
                success=False,
                error=f"Tool execution error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Record for loop detection
        if agent_id:
            from app.main import get_loop_detection_service

            loop_service = get_loop_detection_service()
            if loop_service:
                import hashlib

                output_hash = hashlib.md5(result.to_json().encode()).hexdigest()
                loop_service.record_tool_call(agent_id, tool_name, params, output_hash)

        if task_id:
            await self._log_tool_call(
                task_id=task_id,
                agent_id=agent_id,
                tool_name=tool_name,
                tool_type="internal",
                params=params,
                result=result,
            )

        return result

    async def execute_tool_call(
        self,
        tool_call: ToolCall,
        agent_id: UUID | None = None,
        task_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Execute a tool call from LLM response.

        Routes automatically:
          - mcp__{server}__{tool}  → MCP server
          - anything else          → built-in ToolRegistry
        """
        if tool_call.name.startswith("mcp__"):
            content = await self._execute_mcp_tool(
                qualified_name=tool_call.name,
                args=tool_call.arguments,
                agent_id=agent_id,
                task_id=task_id,
            )
        else:
            result = await self.execute_tool(
                tool_name=tool_call.name,
                params=tool_call.arguments,
                agent_id=agent_id,
                task_id=task_id,
            )
            content = self._format_result_for_llm(tool_call.name, result)

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.name,
            "content": content,
        }

    async def _execute_mcp_tool(
        self,
        qualified_name: str,
        args: dict[str, Any],
        agent_id: UUID | None = None,
        task_id: UUID | None = None,
    ) -> str:
        """Route a mcp__{server}__{tool} call to the correct MCP server."""
        parts = qualified_name.split("__", 2)
        if len(parts) != 3:
            return f"Invalid MCP tool name: '{qualified_name}'. Expected mcp__server__tool."
        _, server_safe, tool_name = parts

        # Find matching server (compare safe names)
        mcp_result = await self.session.execute(
            select(MCPServer).where(MCPServer.enabled == True)  # noqa: E712
        )
        server = None
        for s in mcp_result.scalars().all():
            if _server_safe_name(s.name) == server_safe:
                server = s
                break

        if not server:
            return f"MCP server '{server_safe}' not found or disabled."

        start = time.time()
        try:
            if server.server_type == "http":
                result_text = await call_tool_http(
                    server.url, tool_name, args, server.headers
                )
            elif server.server_type == "sse":
                result_text = await call_tool_sse(
                    server.url, tool_name, args, server.headers
                )
            elif server.server_type == "stdio":
                result_text = await call_tool_stdio(
                    server.command, server.args, tool_name, args, server.env_vars
                )
            else:
                return f"Unsupported server_type: '{server.server_type}'."

            duration_ms = int((time.time() - start) * 1000)

            if task_id:
                task_service = TaskService(self.session)
                await task_service.add_tool_call(
                    task_id=task_id,
                    tool_name=f"{server.name}/{tool_name}",
                    tool_type="mcp",
                    input_data=args,
                    output_data={"result": (result_text or "")[:500]},
                    duration_ms=duration_ms,
                    success=True,
                    agent_id=agent_id
                    if agent_id
                    else UUID("00000000-0000-0000-0000-000000000000"),
                )

            return result_text or "(empty response from MCP server)"

        except Exception as e:
            return f"MCP tool '{server.name}/{tool_name}' failed: {e}"

    def _format_result_for_llm(self, tool_name: str, result: ToolResult) -> str:
        """Format built-in tool result for LLM consumption."""
        if not result.success:
            return f"Tool '{tool_name}' failed: {result.error}"

        tool = self.tool_registry.get(tool_name)
        if tool:
            return tool.format_result(result)

        if result.data:
            if isinstance(result.data, (dict, list)):
                return json.dumps(result.data, indent=2, default=str)
            return str(result.data)

        if result.stdout:
            return result.stdout

        return f"Tool '{tool_name}' executed successfully."

    async def _log_tool_call(
        self,
        task_id: UUID,
        agent_id: UUID | None,
        tool_name: str,
        tool_type: str,
        params: dict[str, Any],
        result: ToolResult,
    ) -> None:
        """Log tool call to task events."""
        task_service = TaskService(self.session)

        payload = {
            "tool_name": tool_name,
            "params": params,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
        }
        if not result.success:
            payload["error"] = result.error
        elif result.data:
            data_str = json.dumps(result.data, default=str)
            payload["result_summary"] = (
                data_str[:500] + "..." if len(data_str) > 500 else data_str
            )

        await task_service.add_tool_call(
            task_id=task_id,
            tool_name=tool_name,
            tool_type=tool_type,
            input_data=params,
            output_data=result.data if result.success else {"error": result.error},
            duration_ms=result.execution_time_ms,
            success=result.success,
            agent_id=agent_id
            if agent_id
            else UUID("00000000-0000-0000-0000-000000000000"),
        )

    # -------------------------------------------------------------------------
    # LLM + Tools Loop
    # -------------------------------------------------------------------------

    async def run_with_tools(
        self,
        llm_config_id: UUID,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        max_iterations: int = 5,
        agent_id: UUID | None = None,
        task_id: UUID | None = None,
    ) -> LlmResponse:
        """
        Run LLM completion with tool calling loop.

        Uses get_tool_definitions_async() to include both built-in and MCP tools,
        filtered by enabled status.
        """
        llm_service = LLMService(self.session)

        # Get all available tools (built-in + MCP, respecting enabled flag)
        tools = await self.get_tool_definitions_async()

        iteration = 0
        current_messages = list(messages)

        while iteration < max_iterations:
            iteration += 1

            response = await llm_service.complete(
                config_id=llm_config_id,
                messages=current_messages,
                tools=tools if tools else None,
                system_prompt=system_prompt,
                agent_id=agent_id,
                task_id=task_id,
            )

            if not response.has_tool_calls:
                return response

            # Append assistant message with tool calls
            current_messages.append(
                {
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in response.tool_calls
                    ],
                }
            )

            # Execute all tool calls (built-in + MCP)
            for tool_call in response.tool_calls:
                tool_message = await self.execute_tool_call(
                    tool_call=tool_call,
                    agent_id=agent_id,
                    task_id=task_id,
                )
                current_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.name,
                        "content": tool_message["content"],
                    }
                )

        # Max iterations reached — final response without tools
        return await llm_service.complete(
            config_id=llm_config_id,
            messages=current_messages,
            system_prompt=system_prompt,
            agent_id=agent_id,
            task_id=task_id,
        )
