"""
Tasks API Endpoints - Kanban Board Support
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import get_current_user
from ...database import get_session
from ...models.enums import PriorityEnum, TaskStatusEnum
from ...models.user import User
from ...services import TaskService

router = APIRouter()


@router.get("/tasks", response_model=dict)
async def list_tasks(
    status: TaskStatusEnum | None = None,
    priority: PriorityEnum | None = None,
    domain: str | None = None,
    assigned_agent_id: UUID | None = None,
    parent_task_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List tasks with filters - supports Kanban board"""
    service = TaskService(session)

    tasks = await service.get_tasks(
        status=status,
        priority=priority,
        domain_hint=domain,
        assigned_agent_id=assigned_agent_id,
        skip=skip,
        limit=limit,
    )

    return {
        "data": tasks,
        "meta": {
            "page": skip // limit + 1,
            "limit": limit,
            "total": len(tasks),
        },
    }


@router.post("/tasks", response_model=dict)
async def create_task(
    task_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new task"""
    service = TaskService(session)

    task = await service.create_task(
        title=task_data["title"],
        description=task_data.get("description", ""),
        priority=PriorityEnum(task_data.get("priority", "MEDIUM")),
        domain_hint=task_data.get("domain_hint"),
        assigned_agent_id=UUID(task_data["assigned_agent_id"])
        if task_data.get("assigned_agent_id")
        else None,
        parent_task_id=UUID(task_data["parent_task_id"])
        if task_data.get("parent_task_id")
        else None,
        created_by=task_data.get("created_by", "user"),
    )

    return {"data": task}


@router.get("/tasks/{task_id}", response_model=dict)
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

    return {
        "data": {
            **task.__dict__,
            "subtasks": subtasks,
            "events": events,
        },
    }


@router.patch("/tasks/{task_id}/status", response_model=dict)
async def update_task_status(
    task_id: UUID,
    status_update: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update task status (Kanban column move)"""
    service = TaskService(session)

    agent_id = (
        UUID(status_update["agent_id"]) if status_update.get("agent_id") else None
    )

    task = await service.update_task_status(
        task_id=task_id,
        new_status=TaskStatusEnum(status_update["status"]),
        agent_id=agent_id,
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"data": task}


@router.patch("/tasks/{task_id}/assign", response_model=dict)
async def assign_task(
    task_id: UUID,
    assignment: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Assign task to agent"""
    service = TaskService(session)

    task = await service.assign_task(
        task_id=task_id,
        agent_id=UUID(assignment["agent_id"]),
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task or agent not found")

    return {"data": task}


@router.post("/tasks/{task_id}/events", response_model=dict)
async def add_task_event(
    task_id: UUID,
    event_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add event to task history"""
    from ...models.enums import TaskEventTypeEnum

    service = TaskService(session)

    agent_id = UUID(event_data["agent_id"]) if event_data.get("agent_id") else None

    event = await service.create_task_event(
        task_id=task_id,
        event_type=TaskEventTypeEnum(event_data["type"]),
        payload=event_data.get("payload", {}),
        agent_id=agent_id,
    )

    return {"data": event}


# Subtask endpoints


@router.post("/tasks/{task_id}/subtasks", response_model=dict)
async def create_subtask(
    task_id: UUID,
    subtask_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a subtask under a parent task"""
    service = TaskService(session)

    subtask = await service.create_task(
        title=subtask_data["title"],
        description=subtask_data.get("description", ""),
        priority=PriorityEnum(subtask_data.get("priority", "MEDIUM")),
        domain_hint=subtask_data.get("domain_hint"),
        parent_task_id=task_id,
        created_by=subtask_data.get("created_by", "user"),
    )

    return {"data": subtask}


# Kanban board view


@router.get("/tasks/kanban/board", response_model=dict)
async def get_kanban_board(
    domain: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Get all tasks organized by status for Kanban view"""
    service = TaskService(session)

    # Get all tasks
    tasks = await service.get_tasks(domain_hint=domain, limit=1000)

    # Organize by status
    columns = {
        "backlog": [],
        "in_progress": [],
        "done": [],
        "failed": [],
    }

    for task in tasks:
        status_map = {
            TaskStatusEnum.BACKLOG: "backlog",
            TaskStatusEnum.IN_PROGRESS: "in_progress",
            TaskStatusEnum.DONE: "done",
            TaskStatusEnum.FAILED: "failed",
        }
        column = status_map.get(task.status, "backlog")
        columns[column].append(task)

    return {"data": columns}


# Task stats


@router.get("/tasks/stats/overview", response_model=dict)
async def get_task_stats(
    session: AsyncSession = Depends(get_session),
):
    """Get task statistics"""
    service = TaskService(session)
    stats = await service.get_task_stats()

    return {"data": stats}
