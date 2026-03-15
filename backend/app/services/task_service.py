"""
Task Service - Business logic for task management
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from ..models.task import Task, TaskEvent
from ..models.enums import TaskStatusEnum, TaskEventTypeEnum, PriorityEnum


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        title: str,
        description: str,
        priority: PriorityEnum = PriorityEnum.MEDIUM,
        domain_hint: Optional[str] = None,
        assigned_agent_id: Optional[UUID] = None,
        parent_task_id: Optional[UUID] = None,
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
            payload={"title": title, "description": description, "priority": priority.value},
        )
        
        # If assigned, create ASSIGNED event
        if assigned_agent_id:
            await self.create_task_event(
                task_id=task.id,
                event_type=TaskEventTypeEnum.ASSIGNED,
                payload={"agent_id": str(assigned_agent_id)},
                agent_id=assigned_agent_id,
            )
            task.status = TaskStatusEnum.IN_PROGRESS
            await self.session.commit()
        
        return task

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get task by ID"""
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        status: Optional[TaskStatusEnum] = None,
        assigned_agent_id: Optional[UUID] = None,
        domain_hint: Optional[str] = None,
        priority: Optional[PriorityEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """Get tasks with optional filters"""
        query = select(Task)
        
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

    async def update_task_status(
        self,
        task_id: UUID,
        new_status: TaskStatusEnum,
        agent_id: Optional[UUID] = None,
    ) -> Optional[Task]:
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
                payload={"old_status": old_status.value, "new_status": new_status.value},
                agent_id=agent_id,
            )
        
        await self.session.refresh(task)
        return task

    async def assign_task(
        self,
        task_id: UUID,
        agent_id: UUID,
    ) -> Optional[Task]:
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
        
        await self.session.refresh(task)
        return task

    async def create_task_event(
        self,
        task_id: UUID,
        event_type: TaskEventTypeEnum,
        payload: dict,
        agent_id: Optional[UUID] = None,
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
    ) -> List[TaskEvent]:
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
        iteration: Optional[int] = None,
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

    async def get_subtasks(self, parent_task_id: UUID) -> List[Task]:
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
