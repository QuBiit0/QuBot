"""
Tool Execution Service - Execute tools and integrate with LLM providers
"""

import json
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.providers import LlmResponse, ToolCall
from ..core.tools import (
    ToolDefinition,
    ToolResult,
    get_tool_registry,
)
from .llm_service import LLMService
from .task_service import TaskService


class ToolExecutionService:
    """
    Service for executing tools and managing tool-LLM interactions.

    Handles:
    - Tool execution with proper error handling
    - Tool result formatting for LLM consumption
    - Tool call tracking
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tool_registry = get_tool_registry()

    async def execute_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        agent_id: UUID | None = None,
        task_id: UUID | None = None,
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters
            agent_id: Optional agent ID for logging
            task_id: Optional task ID for logging

        Returns:
            ToolResult with execution outcome
        """
        # Get tool from registry
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
            )

        # Validate parameters
        is_valid, error = tool.validate_params(params)
        if not is_valid:
            return ToolResult(
                success=False,
                error=f"Parameter validation failed: {error}",
            )

        # Execute
        start_time = time.time()
        try:
            result = await tool.execute(**params)
        except Exception as e:
            result = ToolResult(
                success=False,
                error=f"Tool execution error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Log tool call (if task_id provided)
        if task_id:
            await self._log_tool_call(
                task_id=task_id,
                agent_id=agent_id,
                tool_name=tool_name,
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

        Args:
            tool_call: ToolCall from LLM
            agent_id: Optional agent ID
            task_id: Optional task ID

        Returns:
            Message dict for LLM conversation
        """
        result = await self.execute_tool(
            tool_name=tool_call.name,
            params=tool_call.arguments,
            agent_id=agent_id,
            task_id=task_id,
        )

        # Format result for LLM
        content = self._format_result_for_llm(tool_call.name, result)

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.name,
            "content": content,
        }

    def _format_result_for_llm(self, tool_name: str, result: ToolResult) -> str:
        """Format tool result for LLM consumption"""
        if not result.success:
            return f"Tool '{tool_name}' failed: {result.error}"

        # Use tool's format method if available
        tool = self.tool_registry.get(tool_name)
        if tool:
            return tool.format_result(result)

        # Default formatting
        if result.data:
            if isinstance(result.data, dict):
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
        params: dict[str, Any],
        result: ToolResult,
    ) -> None:
        """Log tool call to task events"""
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
            # Limit data size in log
            data_str = json.dumps(result.data, default=str)
            payload["result_summary"] = (
                data_str[:500] + "..." if len(data_str) > 500 else data_str
            )

        await task_service.add_tool_call(
            task_id=task_id,
            tool_name=tool_name,
            tool_type="internal",
            input_data=params,
            output_data=result.data if result.success else {"error": result.error},
            duration_ms=result.execution_time_ms,
            success=result.success,
            agent_id=agent_id,
        )

    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get all registered tools formatted for LLM"""
        return self.tool_registry.get_tools_for_llm()

    def get_tool_definitions(self) -> list[ToolDefinition]:
        """Get ToolDefinition objects for all registered tools"""
        definitions = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool:
                schema = tool.get_schema()
                func = schema["function"]

                # Convert to ToolDefinition
                definitions.append(
                    ToolDefinition(
                        name=func["name"],
                        description=func["description"],
                        parameters=func["parameters"],
                    )
                )

        return definitions

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

        Args:
            llm_config_id: LLM configuration to use
            messages: Initial messages
            system_prompt: Optional system prompt
            max_iterations: Max tool call iterations
            agent_id: Optional agent ID
            task_id: Optional task ID

        Returns:
            Final LlmResponse
        """
        llm_service = LLMService(self.session)

        # Get available tools
        tools = self.get_tool_definitions()

        iteration = 0
        current_messages = list(messages)

        while iteration < max_iterations:
            iteration += 1

            # Get completion from LLM
            response = await llm_service.complete(
                config_id=llm_config_id,
                messages=current_messages,
                tools=tools if tools else None,
                system_prompt=system_prompt,
                agent_id=agent_id,
                task_id=task_id,
            )

            # If no tool calls, we're done
            if not response.has_tool_calls:
                return response

            # Add assistant message with tool calls
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

            # Execute each tool call
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

        # Max iterations reached, get final response without tools
        return await llm_service.complete(
            config_id=llm_config_id,
            messages=current_messages,
            system_prompt=system_prompt,
            agent_id=agent_id,
            task_id=task_id,
        )
