"""
Tasks API Endpoints - Kanban Board Support
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import get_current_user
from ...database import get_session
from ...models.enums import PriorityEnum, TaskEventTypeEnum, TaskStatusEnum
from ...models.task import Task
from ...models.user import User
from ...schemas.tasks import (
    SubtaskCreateRequest,
    TaskAssignRequest,
    TaskCreateRequest,
    TaskEventRequest,
    TaskStatusUpdateRequest,
)
from ...services import TaskService
from ...services.task_service import serialize_task

router = APIRouter()


@router.get("/tasks", response_model=None)
async def list_tasks(
    status: TaskStatusEnum | None = None,
    priority: PriorityEnum | None = None,
    domain: str | None = None,
    assigned_agent_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List tasks with filters - supports Kanban board"""
    service = TaskService(session)

    tasks, total = await service.get_tasks_with_count(
        status=status,
        priority=priority,
        domain_hint=domain,
        assigned_agent_id=assigned_agent_id,
        skip=skip,
        limit=limit,
    )

    return {
        "data": [serialize_task(t) for t in tasks],
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }


@router.post("/tasks", response_model=None, status_code=201)
async def create_task(
    task_data: TaskCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new task"""
    service = TaskService(session)

    task = await service.create_task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        domain_hint=task_data.domain_hint,
        assigned_agent_id=task_data.assigned_agent_id,
        parent_task_id=task_data.parent_task_id,
        created_by=str(current_user.id),
    )

    return {"data": serialize_task(task)}


@router.get("/tasks/{task_id}", response_model=None)
async def get_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get task by ID with subtasks and events"""
    service = TaskService(session)

    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    subtasks = await service.get_subtasks(task_id)
    events = await service.get_task_events(task_id)

    task_dict = serialize_task(task)
    task_dict["subtasks"] = [serialize_task(s) for s in subtasks]
    task_dict["events"] = [e.model_dump() for e in events]

    return {"data": task_dict}


@router.post("/tasks/{task_id}/run", response_model=None)
async def run_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Submit a task to the worker queue for execution.

    The task must be assigned to an agent first.
    If the task is in BACKLOG, it will be moved to IN_PROGRESS automatically.
    """
    service = TaskService(session)

    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.assigned_agent_id:
        raise HTTPException(
            status_code=400,
            detail="Task must be assigned to an agent before it can be run",
        )

    try:
        from ...worker import submit_task_to_queue

        msg_id = await submit_task_to_queue(task_id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Worker queue unavailable: {exc}",
        ) from exc

    # Move to IN_PROGRESS if still in BACKLOG (skip queue re-submit inside service)
    if task.status == TaskStatusEnum.BACKLOG:
        task.status = TaskStatusEnum.IN_PROGRESS
        await session.commit()
        await service.create_task_event(
            task_id=task_id,
            event_type=TaskEventTypeEnum.STARTED,
            payload={"triggered_by": str(current_user.id)},
        )

    return {"data": {"queued": True, "msg_id": str(msg_id)}}


@router.post("/tasks/{task_id}/cancel", response_model=None)
async def cancel_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel a running task (moves it to FAILED and resets the agent to IDLE)."""
    from ...services.execution_service import ExecutionService

    svc = ExecutionService(session)
    cancelled = await svc.cancel_execution(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Task not found or not in-progress")

    task = await TaskService(session).get_task(task_id)
    return {"data": serialize_task(task) if task else None}


@router.patch("/tasks/{task_id}/status", response_model=None)
async def update_task_status(
    task_id: UUID,
    status_update: TaskStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update task status (Kanban column move)"""
    service = TaskService(session)

    task = await service.update_task_status(
        task_id=task_id,
        new_status=status_update.status,
        agent_id=status_update.agent_id,
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"data": serialize_task(task)}


@router.patch("/tasks/{task_id}/assign", response_model=None)
async def assign_task(
    task_id: UUID,
    assignment: TaskAssignRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Assign task to agent"""
    service = TaskService(session)

    task = await service.assign_task(
        task_id=task_id,
        agent_id=assignment.agent_id,
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task or agent not found")

    return {"data": serialize_task(task)}


@router.post("/tasks/{task_id}/events", response_model=None, status_code=201)
async def add_task_event(
    task_id: UUID,
    event_data: TaskEventRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add event to task history"""
    service = TaskService(session)

    event = await service.create_task_event(
        task_id=task_id,
        event_type=TaskEventTypeEnum(event_data.event_type),
        payload=event_data.payload,
        agent_id=event_data.agent_id,
    )

    return {"data": event}


# Subtask endpoints


@router.post("/tasks/{task_id}/subtasks", response_model=None, status_code=201)
async def create_subtask(
    task_id: UUID,
    subtask_data: SubtaskCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a subtask under a parent task"""
    service = TaskService(session)

    subtask = await service.create_task(
        title=subtask_data.title,
        description=subtask_data.description,
        priority=subtask_data.priority,
        parent_task_id=task_id,
        created_by=str(current_user.id),
    )

    return {"data": subtask}


# Kanban board view


@router.get("/tasks/kanban/board", response_model=None)
async def get_kanban_board(
    domain: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Get all tasks organized by status for Kanban view"""
    service = TaskService(session)

    tasks = await service.get_tasks(domain_hint=domain, limit=1000)

    columns: dict[str, list] = {
        "backlog": [],
        "in_progress": [],
        "done": [],
        "failed": [],
    }

    status_map = {
        TaskStatusEnum.BACKLOG: "backlog",
        TaskStatusEnum.IN_PROGRESS: "in_progress",
        TaskStatusEnum.DONE: "done",
        TaskStatusEnum.FAILED: "failed",
    }

    for task in tasks:
        column = status_map.get(task.status, "backlog")
        columns[column].append(task)

    return {"data": columns}


# Task stats


@router.get("/tasks/stats/overview", response_model=None)
async def get_task_stats(
    session: AsyncSession = Depends(get_session),
):
    """Get task statistics"""
    service = TaskService(session)
    stats = await service.get_task_stats()

    return {"data": stats}
