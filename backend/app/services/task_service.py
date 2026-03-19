"""
Task Service - Business logic for task management
"""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import desc, select

from ..models.enums import PriorityEnum, TaskEventTypeEnum, TaskStatusEnum
from ..models.task import Task, TaskEvent

logger = structlog.get_logger(__name__)


async def _broadcast_task_event(event_type: str, payload: dict[str, Any]) -> None:
    """Fire-and-forget realtime broadcast. Never raises."""
    try:
        from ..core.realtime import EventType, RealtimeEvent, get_connection_manager

        et = EventType(event_type)
        event = RealtimeEvent.create(event_type=et, payload=payload)
        await get_connection_manager().publish_event(event)
    except Exception as exc:
        logger.debug("broadcast_task_event_failed", event=event_type, error=str(exc))


def serialize_task(task: Task) -> dict[str, Any]:
    """
    Convert a Task (with optionally loaded assigned_agent relationship) into
    a frontend-ready dict that includes the nested ``assigned_to`` object.
    """
    d = task.model_dump()
    agent = getattr(task, "assigned_agent", None)
    if agent is not None:
        d["assigned_to"] = {"id": str(agent.id), "name": agent.name}
        d["assigned_agent_name"] = agent.name
    else:
        d["assigned_to"] = None
        d["assigned_agent_name"] = None
    return d


async def _enqueue_task(task_id: UUID) -> None:
    """
    Submit a task to the Redis Streams worker queue.
    Silently logs on failure so the API call still succeeds if Redis is down.
    """
    try:
        from ..worker import submit_task_to_queue

        msg_id = await submit_task_to_queue(task_id)
        logger.info("task_enqueued", task_id=str(task_id), msg_id=str(msg_id))
    except Exception as exc:
        logger.warning(
            "task_enqueue_failed",
            task_id=str(task_id),
            error=str(exc),
        )


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        title: str,
        description: str,
        priority: PriorityEnum = PriorityEnum.MEDIUM,
        domain_hint: str | None = None,
        assigned_agent_id: UUID | None = None,
        parent_task_id: UUID | None = None,
        created_by: str = "user",
    ) -> Task:
        """Create a new task"""
        task = Task(
            title=title,
            description=description,
            status=TaskStatusEnum.BACKLOG,
            priority=priority,
            domain_hint=domain_hint,
            assigned_agent_id=assigned_agent_id,
            parent_task_id=parent_task_id,
            created_by=created_by,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)

        # Create CREATED event
        await self.create_task_event(
            task_id=task.id,
            event_type=TaskEventTypeEnum.CREATED,
            payload={
                "title": title,
                "description": description,
                "priority": priority.value,
            },
        )

        # If assigned, create ASSIGNED event and queue for execution
        if assigned_agent_id:
            await self.create_task_event(
                task_id=task.id,
                event_type=TaskEventTypeEnum.ASSIGNED,
                payload={"agent_id": str(assigned_agent_id)},
                agent_id=assigned_agent_id,
            )
            task.status = TaskStatusEnum.IN_PROGRESS
            await self.session.commit()
            await _enqueue_task(task.id)

        return task

    async def get_task(self, task_id: UUID) -> Task | None:
        """Get task by ID (with assigned_agent eagerly loaded)"""
        result = await self.session.execute(
            select(Task)
            .options(selectinload(Task.assigned_agent))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        status: TaskStatusEnum | None = None,
        assigned_agent_id: UUID | None = None,
        domain_hint: str | None = None,
        priority: PriorityEnum | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Get tasks with optional filters"""
        query = select(Task).options(selectinload(Task.assigned_agent))

        if status:
            query = query.where(Task.status == status)
        if assigned_agent_id:
            query = query.where(Task.assigned_agent_id == assigned_agent_id)
        if domain_hint:
            query = query.where(Task.domain_hint == domain_hint)
        if priority:
            query = query.where(Task.priority == priority)

        query = query.order_by(desc(Task.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_tasks(
        self,
        status: TaskStatusEnum | None = None,
        assigned_agent_id: UUID | None = None,
        domain_hint: str | None = None,
        priority: PriorityEnum | None = None,
    ) -> int:
        """Return total number of tasks matching the given filters"""
        query = select(func.count()).select_from(Task)
        if status:
            query = query.where(Task.status == status)
        if assigned_agent_id:
            query = query.where(Task.assigned_agent_id == assigned_agent_id)
        if domain_hint:
            query = query.where(Task.domain_hint == domain_hint)
        if priority:
            query = query.where(Task.priority == priority)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_tasks_with_count(
        self,
        status: TaskStatusEnum | None = None,
        assigned_agent_id: UUID | None = None,
        domain_hint: str | None = None,
        priority: PriorityEnum | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        """Get paginated tasks and total count"""
        tasks = await self.get_tasks(
            status=status,
            assigned_agent_id=assigned_agent_id,
            domain_hint=domain_hint,
            priority=priority,
            skip=skip,
            limit=limit,
        )
        total = await self.count_tasks(
            status=status,
            assigned_agent_id=assigned_agent_id,
            domain_hint=domain_hint,
            priority=priority,
        )
        return tasks, total

    async def update_task_status(
        self,
        task_id: UUID,
        new_status: TaskStatusEnum,
        agent_id: UUID | None = None,
    ) -> Task | None:
        """Update task status and create event"""
        task = await self.get_task(task_id)
        if not task:
            return None

        old_status = task.status
        task.status = new_status

        if new_status in [TaskStatusEnum.DONE, TaskStatusEnum.FAILED]:
            task.completed_at = datetime.utcnow()

        await self.session.commit()

        # Create status change event
        event_type_map = {
            TaskStatusEnum.IN_PROGRESS: TaskEventTypeEnum.STARTED,
            TaskStatusEnum.DONE: TaskEventTypeEnum.COMPLETED,
            TaskStatusEnum.FAILED: TaskEventTypeEnum.FAILED,
        }

        event_type = event_type_map.get(new_status)
        if event_type:
            await self.create_task_event(
                task_id=task_id,
                event_type=event_type,
                payload={
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                },
                agent_id=agent_id,
            )

        # Queue task for execution when moved to IN_PROGRESS
        if new_status == TaskStatusEnum.IN_PROGRESS and task.assigned_agent_id:
            await _enqueue_task(task_id)

        await self.session.refresh(task)

        # Broadcast real-time update
        ws_event = {
            TaskStatusEnum.DONE: "task.completed",
            TaskStatusEnum.FAILED: "task.failed",
        }.get(new_status, "task.updated")
        await _broadcast_task_event(ws_event, {
            "task_id": str(task_id),
            "status": new_status.value,
        })

        return task

    async def assign_task(
        self,
        task_id: UUID,
        agent_id: UUID,
    ) -> Task | None:
        """Assign task to an agent"""
        task = await self.get_task(task_id)
        if not task:
            return None

        task.assigned_agent_id = agent_id
        task.status = TaskStatusEnum.IN_PROGRESS

        await self.session.commit()

        # Create assignment event
        await self.create_task_event(
            task_id=task_id,
            event_type=TaskEventTypeEnum.ASSIGNED,
            payload={"agent_id": str(agent_id)},
            agent_id=agent_id,
        )

        # Submit to execution queue
        await _enqueue_task(task_id)

        await self.session.refresh(task)

        # Broadcast assignment
        await _broadcast_task_event("task.assigned", {
            "task_id": str(task_id),
            "agent_id": str(agent_id),
            "status": TaskStatusEnum.IN_PROGRESS.value,
        })

        return task

    async def create_task_event(
        self,
        task_id: UUID,
        event_type: TaskEventTypeEnum,
        payload: dict,
        agent_id: UUID | None = None,
    ) -> TaskEvent:
        """Create a task event (audit log)"""
        event = TaskEvent(
            task_id=task_id,
            type=event_type,
            payload=payload,
            agent_id=agent_id,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_task_events(
        self,
        task_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TaskEvent]:
        """Get events for a task"""
        result = await self.session.execute(
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id)
            .order_by(desc(TaskEvent.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def add_progress_update(
        self,
        task_id: UUID,
        message: str,
        agent_id: UUID,
        iteration: int | None = None,
    ) -> TaskEvent:
        """Add a progress update event"""
        payload = {"message": message}
        if iteration is not None:
            payload["iteration"] = iteration

        return await self.create_task_event(
            task_id=task_id,
            event_type=TaskEventTypeEnum.PROGRESS_UPDATE,
            payload=payload,
            agent_id=agent_id,
        )

    async def add_tool_call(
        self,
        task_id: UUID,
        tool_name: str,
        tool_type: str,
        input_data: dict,
        output_data: dict,
        duration_ms: int,
        success: bool,
        agent_id: UUID,
    ) -> TaskEvent:
        """Log a tool call event"""
        return await self.create_task_event(
            task_id=task_id,
            event_type=TaskEventTypeEnum.TOOL_CALL,
            payload={
                "tool_name": tool_name,
                "tool_type": tool_type,
                "input": input_data,
                "output": output_data,
                "duration_ms": duration_ms,
                "success": success,
            },
            agent_id=agent_id,
        )

    async def get_subtasks(self, parent_task_id: UUID) -> list[Task]:
        """Get subtasks of a parent task"""
        result = await self.session.execute(
            select(Task).where(Task.parent_task_id == parent_task_id)
        )
        return result.scalars().all()

    async def get_task_stats(self) -> dict:
        """Get task statistics"""
        stats = {}
        for status in TaskStatusEnum:
            result = await self.session.execute(
                select(Task).where(Task.status == status)
            )
            stats[status.value] = len(result.scalars().all())
        return stats
