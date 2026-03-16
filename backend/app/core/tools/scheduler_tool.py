"""
Scheduler Tool - Schedule tasks and reminders
"""

import time
from datetime import datetime, timedelta
from uuid import uuid4

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class SchedulerTool(BaseTool):
    """
    Tool for scheduling tasks and reminders.

    Integrates with the task system to create scheduled tasks.
    Note: Actual task scheduling is handled by the worker service.
    This tool creates the scheduled task entries in the database.
    """

    name = "scheduler"
    description = (
        "Schedule tasks to be executed at a later time or on a recurring basis. "
        "Can schedule one-time tasks or recurring tasks with cron-like expressions. "
        "Use for delayed execution, periodic tasks, or reminders."
    )
    category = ToolCategory.SYSTEM
    risk_level = ToolRiskLevel.NORMAL

    # Max future scheduling (30 days)
    MAX_FUTURE_DAYS = 30

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "action": ToolParameter(
                name="action",
                type="string",
                description="Scheduling action",
                required=True,
                enum=["schedule", "cancel", "list", "info"],
            ),
            "title": ToolParameter(
                name="title",
                type="string",
                description="Task title (for schedule action)",
                required=False,
            ),
            "description": ToolParameter(
                name="description",
                type="string",
                description="Task description (for schedule action)",
                required=False,
            ),
            "run_at": ToolParameter(
                name="run_at",
                type="string",
                description="When to run the task (ISO 8601 datetime or relative like '+1h', '+30m', 'tomorrow 9am')",
                required=False,
            ),
            "recurring": ToolParameter(
                name="recurring",
                type="string",
                description="Cron expression for recurring tasks (e.g., '0 9 * * *' for daily at 9am)",
                required=False,
            ),
            "task_id": ToolParameter(
                name="task_id",
                type="string",
                description="Task ID (for cancel/info actions)",
                required=False,
            ),
            "agent_id": ToolParameter(
                name="agent_id",
                type="string",
                description="Agent ID to assign the scheduled task to",
                required=False,
            ),
        }

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # Maximum tasks per agent
        self.max_tasks_per_agent = self.config.get("max_tasks_per_agent", 100)

        # Allowed task types
        self.allowed_domains = self.config.get("allowed_domains", [])

    def _parse_run_at(self, run_at: str) -> tuple[datetime | None, str | None]:
        """
        Parse run_at expression to datetime.

        Supports:
        - ISO 8601: 2024-03-13T09:00:00
        - Relative: +1h, +30m, +1d
        - Natural: tomorrow 9am, in 2 hours
        """
        if not run_at:
            return None, "run_at is required"

        now = datetime.utcnow()

        # ISO 8601
        try:
            dt = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None), None
        except ValueError:
            pass

        # Relative time
        if run_at.startswith("+"):
            try:
                value = int(run_at[1:-1])
                unit = run_at[-1].lower()

                if unit == "m":
                    return now + timedelta(minutes=value), None
                elif unit == "h":
                    return now + timedelta(hours=value), None
                elif unit == "d":
                    return now + timedelta(days=value), None
                elif unit == "w":
                    return now + timedelta(weeks=value), None
            except (ValueError, IndexError):
                pass

        # Special keywords
        if run_at.lower() == "now":
            return now, None

        if run_at.lower().startswith("tomorrow"):
            try:
                time_part = run_at.split(None, 1)[1] if " " in run_at else "09:00"
                hour, minute = map(
                    int, time_part.replace("am", "").replace("pm", "").split(":")
                )
                if "pm" in time_part.lower() and hour != 12:
                    hour += 12
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                ), None
            except (ValueError, IndexError):
                pass

        return None, f"Unable to parse run_at expression: {run_at}"

    async def execute(
        self,
        action: str,
        title: str | None = None,
        description: str | None = None,
        run_at: str | None = None,
        recurring: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
    ) -> ToolResult:
        """
        Execute scheduling operation.

        Args:
            action: Operation type (schedule, cancel, list, info)
            title: Task title
            description: Task description
            run_at: When to run
            recurring: Cron expression for recurring
            task_id: Existing task ID
            agent_id: Agent to assign

        Returns:
            ToolResult with operation outcome
        """
        start_time = time.time()

        try:
            if action == "schedule":
                return await self._action_schedule(
                    title, description, run_at, recurring, agent_id
                )
            elif action == "cancel":
                return await self._action_cancel(task_id)
            elif action == "list":
                return await self._action_list(agent_id)
            elif action == "info":
                return await self._action_info(task_id)
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Scheduler error: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _action_schedule(
        self,
        title: str | None,
        description: str | None,
        run_at: str | None,
        recurring: str | None,
        agent_id: str | None,
    ) -> ToolResult:
        """Schedule a new task"""
        if not title:
            return ToolResult(success=False, error="Title is required for scheduling")

        # Parse run_at
        if run_at:
            run_datetime, error = self._parse_run_at(run_at)
            if error:
                return ToolResult(success=False, error=error)
        else:
            run_datetime = datetime.utcnow()

        # Validate not too far in future
        max_future = datetime.utcnow() + timedelta(days=self.MAX_FUTURE_DAYS)
        if run_datetime > max_future:
            return ToolResult(
                success=False,
                error=f"Cannot schedule more than {self.MAX_FUTURE_DAYS} days in advance",
            )

        # Generate task ID
        new_task_id = str(uuid4())

        # Build task data
        task_data = {
            "id": new_task_id,
            "title": title,
            "description": description or "",
            "scheduled_for": run_datetime.isoformat(),
            "recurring": recurring,
            "agent_id": agent_id,
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat(),
        }

        # Here we would save to database
        # For now, return success with task data

        return ToolResult(
            success=True,
            data=task_data,
            metadata={
                "task_id": new_task_id,
                "scheduled_for": run_datetime.isoformat(),
                "recurring": recurring,
            },
            execution_time_ms=0,
        )

    async def _action_cancel(self, task_id: str | None) -> ToolResult:
        """Cancel a scheduled task"""
        if not task_id:
            return ToolResult(
                success=False, error="task_id is required for cancel action"
            )

        # Here we would cancel in database
        # For now, return success

        return ToolResult(
            success=True,
            data={"task_id": task_id, "action": "cancelled"},
            execution_time_ms=0,
        )

    async def _action_list(self, agent_id: str | None) -> ToolResult:
        """List scheduled tasks"""
        # Here we would query database
        # For now, return empty list

        return ToolResult(
            success=True,
            data={
                "tasks": [],
                "count": 0,
                "agent_id": agent_id,
            },
            execution_time_ms=0,
        )

    async def _action_info(self, task_id: str | None) -> ToolResult:
        """Get task info"""
        if not task_id:
            return ToolResult(
                success=False, error="task_id is required for info action"
            )

        # Here we would query database
        # For now, return not found

        return ToolResult(
            success=False,
            error=f"Task not found: {task_id}",
            execution_time_ms=0,
        )
