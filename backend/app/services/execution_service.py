"""
Execution Service - Core execution engine for agent tasks.

The execution loop now integrates all 5 memory optimization phases:

Phase 1 — Token Budget Manager
  • TokenBudget allocated from LLM model context window
  • ContextAssembler trims each section before building the prompt
  • No more uncapped memory injection

Phase 2 — Context Compaction
  • ContextCompactor tracks token usage per iteration
  • When usage > 80%, compaction is triggered:
      1. Memory flush (extract durable facts via LLM)
      2. Summarize old messages
      3. Keep last KEEP_RECENT_TURNS turns verbatim
  • Tool results are pruned (soft-trim / hard-clear)

Phase 3 — Hybrid Memory Retrieval
  • MemoryService.build_agent_context_sections() uses BM25 + vector +
    temporal decay + MMR to retrieve only the most relevant memories
  • Content is pre-sorted by score so ContextAssembler drops least
    relevant items first when memory budget is tight

Phase 4 — Conversation History (web chat sessions)
  • Chat endpoint persists turns to Redis via ConversationManager
  • Execution loop respects history already loaded upstream

Phase 5 — Memory Consolidation (background)
  • Key facts extracted at task completion → stored via MemoryService
  • MemoryConsolidator is invoked after task completion (fire-and-forget)
"""

import asyncio
import json
import logging
import re
import time
from collections.abc import Callable
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.context_budget import ContextAssembler
from ..core.context_compactor import ContextCompactor
from ..core.providers import FinishReason, LlmResponse
from ..core.token_counter import TokenBudget, count_messages_tokens, count_tokens
from ..models.agent import Agent
from ..models.enums import AgentStatusEnum, TaskEventTypeEnum, TaskStatusEnum
from ..models.task import Task
from .agent_service import AgentService
from .llm_service import LLMService
from .memory_service import MemoryService
from .task_service import TaskService
from .tool_execution_service import ToolExecutionService

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    PAUSED    = "paused"
    CANCELLED = "cancelled"


class ExecutionService:
    """
    Service for executing agent tasks.

    Lifecycle:
        Setup  → load agent, task, memory context with token budget
        Loop   → iterative LLM calls + tool execution + compaction
        Teardown → save results, persist key facts, trigger consolidation
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_service    = TaskService(session)
        self.agent_service   = AgentService(session)
        self.memory_service  = MemoryService(
            session,
            openai_api_key=settings.OPENAI_API_KEY or None,
        )
        self.llm_service     = LLMService(session)
        self.tool_service    = ToolExecutionService(session)

    # ── Public entry point ────────────────────────────────────────────────────

    async def execute_task(
        self,
        task_id: UUID,
        max_iterations: int = 10,
        on_progress: Callable[[str, int], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a task with its assigned agent.

        Returns an execution result dict with status, output, token stats,
        and metadata.
        """
        start_time = time.time()

        task = await self.task_service.get_task(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        if not task.assigned_agent_id:
            return {"success": False, "error": "Task has no assigned agent"}

        agent = await self.agent_service.get_agent(task.assigned_agent_id)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        await self.task_service.update_task_status(
            task_id=task_id,
            new_status=TaskStatusEnum.IN_PROGRESS,
            agent_id=agent.id,
        )
        await self.agent_service.update_agent_status(
            agent_id=agent.id,
            status=AgentStatusEnum.WORKING,
            current_task_id=task_id,
        )

        try:
            context = await self._build_context(agent, task)
            result  = await self._run_agent_loop(
                agent=agent,
                task=task,
                context=context,
                max_iterations=max_iterations,
                on_progress=on_progress,
            )

            if result["success"]:
                await self.task_service.update_task_status(
                    task_id=task_id,
                    new_status=TaskStatusEnum.DONE,
                    agent_id=agent.id,
                )
                # Persist task memory + consolidate in background
                await self.memory_service.create_task_memory(
                    task_id=task_id,
                    summary=result.get("output", "Task completed")[:500],
                    key_facts=result.get("key_facts", []),
                )
                asyncio.create_task(
                    self._background_consolidate(agent.id)
                )
            else:
                await self.task_service.update_task_status(
                    task_id=task_id,
                    new_status=TaskStatusEnum.FAILED,
                    agent_id=agent.id,
                )

            result["execution_time_ms"] = int((time.time() - start_time) * 1000)
            return result

        except Exception as exc:
            logger.exception("execute_task error for task %s: %s", task_id, exc)
            await self.task_service.update_task_status(
                task_id=task_id,
                new_status=TaskStatusEnum.FAILED,
                agent_id=agent.id,
            )
            await self.task_service.create_task_event(
                task_id=task_id,
                event_type=TaskEventTypeEnum.FAILED,
                payload={"error": str(exc)},
                agent_id=agent.id,
            )
            return {
                "success": False,
                "error": str(exc),
                "execution_time_ms": int((time.time() - start_time) * 1000),
            }

        finally:
            await self.agent_service.update_agent_status(
                agent_id=agent.id,
                status=AgentStatusEnum.IDLE,
                current_task_id=None,
            )

    # ── Context building ──────────────────────────────────────────────────────

    async def _build_context(
        self, agent: Agent, task: Task
    ) -> dict[str, Any]:
        """
        Build execution context with budget-aware memory injection.

        Phase 1: Determine TokenBudget for the agent's LLM model.
        Phase 3: Retrieve memories via hybrid search, sorted by relevance.
        Phase 1: Use ContextAssembler to fit each section within its budget.
        """
        # Resolve model name for budget calculation
        model_name = await self._resolve_model_name(agent)
        budget      = TokenBudget(model_name, max_output_tokens=settings.DEFAULT_LLM_MAX_TOKENS)
        assembler   = ContextAssembler(budget)

        # Raw system prompt (before trimming)
        raw_system = self._build_raw_system_prompt(agent, task)
        system_prompt = assembler.fit_system_prompt(raw_system)

        # Hybrid-ranked memory sections → fit within budget
        memory_sections = await self.memory_service.build_agent_context_sections(
            agent_id=agent.id,
            task_title=task.title,
            task_domain=task.domain_hint,
            query=task.description or task.title,
        )
        memory_context = assembler.fit_memory_context(memory_sections)

        # If memory exists, append it after the system prompt
        if memory_context:
            system_prompt = system_prompt + "\n\n" + memory_context

        # Tool definitions
        raw_tools = await self.tool_service.get_tool_definitions_async()
        tools     = assembler.fit_tools(raw_tools, task_hint=task.description or task.title)

        used_tokens = {
            "system": count_tokens(system_prompt, model_name),
            "tools": count_tokens(
                json.dumps([t if isinstance(t, dict) else vars(t) for t in tools], default=str),
                model_name,
            ),
        }

        logger.debug(
            "Context built for task %s:\n%s",
            task.id,
            budget.summary(used_tokens),
        )

        return {
            "agent": {
                "id": str(agent.id),
                "name": agent.name,
                "domain": agent.domain.value if hasattr(agent.domain, "value") else str(agent.domain),
            },
            "task": {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
            },
            "system_prompt": system_prompt,
            "tools": tools,
            "budget": budget,
        }

    def _build_raw_system_prompt(self, agent: Agent, task: Task) -> str:
        """Build the unsized system prompt (may be trimmed by ContextAssembler)."""
        lines = [
            f"You are {agent.name}, a specialized AI agent.",
            f"Domain: {agent.domain}",
            "",
            "Your role:",
            agent.role_description or f"Assist with {agent.domain} tasks",
        ]

        if agent.personality:
            lines.extend(["", "Personality traits:"])
            for trait, value in agent.personality.items():
                lines.append(f"- {trait}: {value}")

        lines.extend([
            "",
            "Current task:",
            f"Title: {task.title}",
            f"Description: {task.description}",
            "",
            "Instructions:",
            "1. Analyze the task carefully",
            "2. Use available tools when needed",
            "3. Provide clear, actionable results",
            "4. If stuck, report failure honestly",
            "",
            "When you complete the task, summarize your work clearly.",
        ])

        return "\n".join(lines)

    async def _resolve_model_name(self, agent: Agent) -> str:
        """Resolve the LLM model name for the agent's llm_config."""
        try:
            if agent.llm_config_id:
                config = await self.llm_service.get_config(agent.llm_config_id)
                if config:
                    return config.model_name
        except Exception:
            pass
        return settings.DEFAULT_LLM_MODEL

    # ── Agent execution loop ──────────────────────────────────────────────────

    async def _run_agent_loop(
        self,
        agent: Agent,
        task: Task,
        context: dict[str, Any],
        max_iterations: int,
        on_progress: Callable[[str, int], None] | None,
    ) -> dict[str, Any]:
        """
        Run the main agent execution loop with Phase 1 + Phase 2 integration.

        Per-iteration:
        1. Report progress
        2. Run LLM with tools
        3. Check token usage → trigger compaction if > 80%
        4. Append response to messages
        5. Check completion condition
        """
        budget: TokenBudget = context["budget"]
        model_name = budget.model_name

        # Initialize compactor (uses LLM for quality summaries if available)
        llm_provider = None
        try:
            llm_provider = await self.llm_service.create_provider(agent.llm_config_id)
        except Exception:
            pass

        compactor = ContextCompactor(llm_provider=llm_provider)

        messages: list[dict] = [
            {"role": "user", "content": f"Task: {task.title}\n\n{task.description}"}
        ]
        compaction_summary: str | None = None
        all_responses: list[LlmResponse] = []
        total_tokens_used = 0

        for iteration in range(max_iterations):
            if on_progress:
                on_progress(f"Iteration {iteration + 1}/{max_iterations}", iteration + 1)

            await self.task_service.add_progress_update(
                task_id=task.id,
                agent_id=agent.id,
                message=f"Processing iteration {iteration + 1}",
                iteration=iteration + 1,
            )

            # ── Phase 1: Fit conversation history within budget ───────────────
            assembler = ContextAssembler(budget)
            fitted_messages, compaction_summary = assembler.fit_conversation_history(
                messages, compaction_summary
            )

            # Inject compaction summary if we have one
            if compaction_summary:
                fitted_messages = compactor.inject_summary(
                    fitted_messages, compaction_summary
                )

            # ── Run LLM ───────────────────────────────────────────────────────
            response = await self.tool_service.run_with_tools(
                llm_config_id=agent.llm_config_id,
                messages=fitted_messages,
                system_prompt=context["system_prompt"],
                max_iterations=1,
                agent_id=agent.id,
                task_id=task.id,
            )

            all_responses.append(response)
            total_tokens_used += response.total_tokens

            # Append assistant response to full history
            if response.content:
                messages.append({"role": "assistant", "content": response.content})

            # ── Phase 2: Check if compaction needed ───────────────────────────
            used = {
                "system":  count_tokens(context["system_prompt"], model_name),
                "history": count_messages_tokens(messages, model_name),
            }
            if budget.is_context_full(used):
                logger.info(
                    "Context full at iteration %d for task %s — compacting",
                    iteration + 1,
                    task.id,
                )
                # Memory flush: extract facts before compacting
                facts = await compactor.extract_key_facts(messages)
                for i, fact in enumerate(facts):
                    try:
                        await self.memory_service.create_agent_memory(
                            agent_id=agent.id,
                            key=f"task_{task.id}_fact_{iteration}_{i}",
                            content=fact,
                            importance=3,
                        )
                    except Exception:
                        pass

                # Compact history
                messages, compaction_summary = await compactor.compact(
                    messages, compaction_summary
                )

            # ── Completion check ──────────────────────────────────────────────
            if self._is_task_complete(response):
                return {
                    "success":    True,
                    "output":     response.content,
                    "iterations": iteration + 1,
                    "total_tokens_used": total_tokens_used,
                    "responses":  self._serialize_responses(all_responses),
                    "key_facts":  self._extract_key_facts(all_responses),
                }

            if (
                not response.has_tool_calls
                and response.finish_reason == FinishReason.STOP
            ):
                return {
                    "success":    True,
                    "output":     response.content,
                    "iterations": iteration + 1,
                    "total_tokens_used": total_tokens_used,
                    "key_facts":  self._extract_key_facts(all_responses),
                }

        return {
            "success":    True,
            "output":     all_responses[-1].content if all_responses else "Max iterations reached",
            "iterations": max_iterations,
            "total_tokens_used": total_tokens_used,
            "note":       "Max iterations reached",
            "key_facts":  self._extract_key_facts(all_responses),
        }

    # ── Background consolidation ──────────────────────────────────────────────

    async def _background_consolidate(self, agent_id: UUID) -> None:
        """
        Fire-and-forget memory consolidation after task completion.
        Runs Phase 5: chunking + dedup + stale cleanup.
        """
        try:
            from .memory_consolidator import MemoryConsolidator
            consolidator = MemoryConsolidator(self.session)
            stats = await consolidator.consolidate_agent(agent_id)
            logger.debug("Post-task consolidation for agent %s: %s", agent_id, stats)
        except Exception as exc:
            logger.debug("Background consolidation skipped: %s", exc)

    # ── Utility methods ───────────────────────────────────────────────────────

    def _is_task_complete(self, response: LlmResponse) -> bool:
        if not response.content:
            return False
        content_lower = response.content.lower()
        return any(
            phrase in content_lower
            for phrase in [
                "task completed",
                "task is complete",
                "i have completed",
                "finished successfully",
                "completed the task",
            ]
        )

    def _extract_key_facts(self, responses: list[LlmResponse]) -> list[str]:
        facts: list[str] = []
        for response in responses:
            if not response.content:
                continue
            for line in response.content.split("\n"):
                line = line.strip()
                if line.startswith(("- ", "* ", "• ", "1. ", "2. ", "3. ")):
                    facts.append(re.sub(r"^[-\s*•\d.]+", "", line).strip())
                elif any(
                    kw in line.lower()
                    for kw in ("result", "found", "discovered", "completed", "created")
                ):
                    facts.append(line)
        return facts[:10]

    def _serialize_responses(
        self, responses: list[LlmResponse]
    ) -> list[dict[str, Any]]:
        return [
            {
                "content":    r.content,
                "tool_calls": [
                    {"name": tc.name, "arguments": tc.arguments}
                    for tc in r.tool_calls
                ],
                "tokens":     r.total_tokens,
            }
            for r in responses
        ]

    async def cancel_execution(self, task_id: UUID) -> bool:
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
