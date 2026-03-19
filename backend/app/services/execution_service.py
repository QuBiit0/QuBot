"""
Execution Service - Core execution engine for agent tasks

This service implements the agent execution loop:
1. Load agent configuration and context
2. Build system prompt with memory injection
3. Execute LLM completion with tool access
4. Handle tool calls and integrate results
5. Continue until task complete or max iterations
"""

import json
import re
import time
from collections.abc import Callable
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.providers import FinishReason, LlmResponse
from ..models.agent import Agent
from ..models.enums import AgentStatusEnum, TaskEventTypeEnum, TaskStatusEnum
from ..models.task import Task
from .agent_service import AgentService
from .llm_service import LLMService
from .memory_service import MemoryService
from .task_service import TaskService
from .tool_execution_service import ToolExecutionService


class ExecutionStatus(Enum):
    """Status of task execution"""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ExecutionService:
    """
    Service for executing agent tasks.

    Manages the complete execution lifecycle:
    - Setup: Load agent, task, and memory context
    - Loop: Iterative LLM calls with tool execution
    - Teardown: Save results and update task status
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_service = TaskService(session)
        self.agent_service = AgentService(session)
        self.memory_service = MemoryService(session)
        self.llm_service = LLMService(session)
        self.tool_service = ToolExecutionService(session)

    async def execute_task(
        self,
        task_id: UUID,
        max_iterations: int = 10,
        on_progress: Callable[[str, int], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a task with an assigned agent.

        Args:
            task_id: Task to execute
            max_iterations: Maximum LLM iterations
            on_progress: Callback for progress updates (message, iteration)

        Returns:
            Execution result with status, output, and metadata
        """
        start_time = time.time()

        # Load task
        task = await self.task_service.get_task(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        if not task.assigned_agent_id:
            return {"success": False, "error": "Task has no assigned agent"}

        # Load agent
        agent = await self.agent_service.get_agent(task.assigned_agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        # Update task status
        await self.task_service.update_task_status(
            task_id=task_id,
            new_status=TaskStatusEnum.IN_PROGRESS,
            agent_id=agent.id,
        )

        # Update agent status
        await self.agent_service.update_agent_status(
            agent_id=agent.id,
            status=AgentStatusEnum.WORKING,
            current_task_id=task_id,
        )

        try:
            # Build execution context
            context = await self._build_context(agent, task)

            # Execute agent loop
            result = await self._run_agent_loop(
                agent=agent,
                task=task,
                context=context,
                max_iterations=max_iterations,
                on_progress=on_progress,
            )

            # Update task with result
            if result["success"]:
                await self.task_service.update_task_status(
                    task_id=task_id,
                    new_status=TaskStatusEnum.DONE,
                    agent_id=agent.id,
                )

                # Create task memory
                await self.memory_service.create_task_memory(
                    task_id=task_id,
                    summary=result.get("output", "Task completed")[:500],
                    key_facts=result.get("key_facts", []),
                )
            else:
                await self.task_service.update_task_status(
                    task_id=task_id,
                    new_status=TaskStatusEnum.FAILED,
                    agent_id=agent.id,
                )

            execution_time = int((time.time() - start_time) * 1000)
            result["execution_time_ms"] = execution_time

            return result

        except Exception as e:
            # Mark task as failed
            await self.task_service.update_task_status(
                task_id=task_id,
                new_status=TaskStatusEnum.FAILED,
                agent_id=agent.id,
            )

            # Log error
            await self.task_service.create_task_event(
                task_id=task_id,
                event_type=TaskEventTypeEnum.FAILED,
                payload={"error": str(e)},
                agent_id=agent.id,
            )

            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000),
            }

        finally:
            # Reset agent status
            await self.agent_service.update_agent_status(
                agent_id=agent.id,
                status=AgentStatusEnum.IDLE,
                current_task_id=None,
            )

    async def _build_context(
        self,
        agent: Agent,
        task: Task,
    ) -> dict[str, Any]:
        """Build execution context with memory injection"""
        context = {
            "agent": {
                "id": str(agent.id),
                "name": agent.name,
                "domain": agent.domain.value if hasattr(agent.domain, "value") else str(agent.domain),
                "personality": agent.personality,
            },
            "task": {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                # input_data is not a DB column — reserved for future enrichment
                "input_data": None,
            },
        }

        # Build system prompt
        system_prompt = await self._build_system_prompt(agent, task)
        context["system_prompt"] = system_prompt

        # Get memory context
        memory_context = await self.memory_service.build_agent_context(
            agent_id=agent.id,
            task_domain=task.domain_hint,
        )
        if memory_context:
            context["memory_context"] = memory_context
            context["system_prompt"] += f"\n\n{memory_context}"

        # Get available tools (built-in + MCP, filtered by enabled)
        tools = await self.tool_service.get_tool_definitions_async()
        context["tools"] = tools

        return context

    async def _build_system_prompt(
        self,
        agent: Agent,
        task: Task,
    ) -> str:
        """Build system prompt for agent"""
        lines = [
            f"You are {agent.name}, a specialized AI agent.",
            f"Domain: {agent.domain}",
            "",
            "Your role:",
            agent.role_description or f"Assist with {agent.domain} tasks",
        ]

        # Add personality traits
        if agent.personality:
            lines.extend(
                [
                    "",
                    "Personality traits:",
                ]
            )
            for trait, value in agent.personality.items():
                lines.append(f"- {trait}: {value}")

        # Add task context
        lines.extend(
            [
                "",
                "Current task:",
                f"Title: {task.title}",
                f"Description: {task.description}",
            ]
        )

        # Add instructions
        lines.extend(
            [
                "",
                "Instructions:",
                "1. Analyze the task carefully",
                "2. Use available tools when needed",
                "3. Provide clear, actionable results",
                "4. If stuck, report failure honestly",
                "",
                "When you complete the task, summarize your work clearly.",
            ]
        )

        return "\n".join(lines)

    async def _run_agent_loop(
        self,
        agent: Agent,
        task: Task,
        context: dict[str, Any],
        max_iterations: int,
        on_progress: Callable[[str, int], None] | None,
    ) -> dict[str, Any]:
        """Run the main agent execution loop"""
        messages = []

        # Add initial user message
        task_message = f"Task: {task.title}\n\n{task.description}"

        messages.append({"role": "user", "content": task_message})

        # Track iterations and results
        all_responses = []

        for iteration in range(max_iterations):
            # Report progress
            if on_progress:
                on_progress(
                    f"Iteration {iteration + 1}/{max_iterations}", iteration + 1
                )

            # Log progress
            await self.task_service.add_progress_update(
                task_id=task.id,
                agent_id=agent.id,
                message=f"Processing iteration {iteration + 1}",
                iteration=iteration + 1,
            )

            # Run LLM with tools
            response = await self.tool_service.run_with_tools(
                llm_config_id=agent.llm_config_id,
                messages=messages,
                system_prompt=context["system_prompt"],
                max_iterations=1,  # We handle the loop here
                agent_id=agent.id,
                task_id=task.id,
            )

            all_responses.append(response)

            # Add assistant response to conversation
            if response.content:
                messages.append({"role": "assistant", "content": response.content})

            # Check if task is complete
            if self._is_task_complete(response):
                return {
                    "success": True,
                    "output": response.content,
                    "iterations": iteration + 1,
                    "responses": [
                        {
                            "content": r.content,
                            "tool_calls": [
                                {"name": tc.name, "arguments": tc.arguments}
                                for tc in r.tool_calls
                            ],
                        }
                        for r in all_responses
                    ],
                    "key_facts": self._extract_key_facts(all_responses),
                }

            # If no tool calls and not complete, continue
            if (
                not response.has_tool_calls
                and response.finish_reason == FinishReason.STOP
            ):
                # LLM thinks it's done
                return {
                    "success": True,
                    "output": response.content,
                    "iterations": iteration + 1,
                    "key_facts": self._extract_key_facts(all_responses),
                }

        # Max iterations reached
        return {
            "success": True,
            "output": all_responses[-1].content
            if all_responses
            else "Max iterations reached",
            "iterations": max_iterations,
            "note": "Max iterations reached",
            "key_facts": self._extract_key_facts(all_responses),
        }

    def _is_task_complete(self, response: LlmResponse) -> bool:
        """Check if response indicates task completion"""
        if not response.content:
            return False

        # Check for completion indicators
        completion_phrases = [
            "task completed",
            "task is complete",
            "i have completed",
            "finished successfully",
            "done",
            "completed the task",
        ]

        content_lower = response.content.lower()
        return any(phrase in content_lower for phrase in completion_phrases)

    def _extract_key_facts(self, responses: list[LlmResponse]) -> list[str]:
        """Extract key facts from responses for memory"""
        facts = []

        for response in responses:
            if response.content:
                # Look for lines with key information
                lines = response.content.split("\n")
                for line in lines:
                    line = line.strip()
                    # Extract lines that look like key findings
                    if line.startswith(("- ", "* ", "• ", "1. ", "2. ", "3. ")):
                        facts.append(re.sub(r"^[-\s*•\d.]+", "", line).strip())
                    elif (
                        "result" in line.lower()
                        or "found" in line.lower()
                        or "discovered" in line.lower()
                    ):
                        facts.append(line)

        # Limit facts
        return facts[:10]

    async def cancel_execution(self, task_id: UUID) -> bool:
        """Cancel a running task execution"""
        # This would require coordination with a running task
        # For now, just update status
        task = await self.task_service.get_task(task_id)
        if not task:
            return False

        if task.status == TaskStatusEnum.IN_PROGRESS:
            await self.task_service.update_task_status(
                task_id=task_id,
                new_status=TaskStatusEnum.FAILED,
            )

            if task.assigned_agent_id:
                await self.agent_service.update_agent_status(
                    agent_id=task.assigned_agent_id,
                    status=AgentStatusEnum.IDLE,
                    current_task_id=None,
                )

        return True
