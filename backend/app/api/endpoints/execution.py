"""
Execution API Endpoints - Agent task execution and orchestration
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import get_current_user
from ...database import get_session
from ...models.user import User
from ...services import AssignmentService, ExecutionService, OrchestratorService

try:
    from ...worker import TaskQueue, submit_task_to_queue

    WORKER_AVAILABLE = True
except ImportError:
    WORKER_AVAILABLE = False
    submit_task_to_queue = None
    TaskQueue = None

router = APIRouter()


@router.post("/tasks/{task_id}/execute", response_model=dict)
async def execute_task(
    task_id: UUID,
    execution_data: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Execute a task immediately (synchronous).

    For long-running tasks, use /tasks/{task_id}/submit instead.

    Request body:
    {
        "max_iterations": 10
    }
    """
    service = ExecutionService(session)

    max_iterations = execution_data.get("max_iterations", 10)

    try:
        result = await service.execute_task(
            task_id=task_id,
            max_iterations=max_iterations,
        )

        return {
            "data": {
                "success": result["success"],
                "output": result.get("output"),
                "iterations": result.get("iterations"),
                "execution_time_ms": result.get("execution_time_ms"),
                "error": result.get("error"),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.post("/tasks/{task_id}/submit", response_model=dict)
async def submit_task_to_worker(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Submit a task to the worker queue for asynchronous execution.

    Use this for long-running tasks that shouldn't block the API.
    """
    if not WORKER_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Worker queue not available. Redis is required."
        )

    from ...services import TaskService

    # Verify task exists
    task_service = TaskService(session)
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Submit to queue
    try:
        msg_id = await submit_task_to_queue(
            task_id=task_id,
            priority=task.priority.value if hasattr(task.priority, "value") else 0,
        )

        return {
            "data": {
                "message_id": msg_id,
                "task_id": str(task_id),
                "status": "queued",
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.post("/tasks/{task_id}/cancel", response_model=dict)
async def cancel_task_execution(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel a running task execution"""
    service = ExecutionService(session)

    success = await service.cancel_execution(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task not found or not running")

    return {
        "data": {
            "task_id": str(task_id),
            "status": "cancelled",
        }
    }


# Orchestrator endpoints


@router.post("/orchestrator/process", response_model=dict)
async def orchestrator_process_task(
    task_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Submit a high-level task to the orchestrator for processing.

    The orchestrator will:
    1. Analyze task complexity
    2. Create appropriate subtasks
    3. Assign agents
    4. Execute and coordinate
    5. Return aggregated results

    Request body:
    {
        "title": "Create a Python API",
        "description": "Build a REST API with FastAPI...",
        "llm_config_id": "uuid",
        "priority": "high|medium|low",
        "domain": "software|data|finance|...",
        "input_data": {}
    }
    """
    service = OrchestratorService(session)

    from ...models.enums import DomainEnum, PriorityEnum

    title = task_data.get("title")
    description = task_data.get("description")
    llm_config_id = UUID(task_data.get("llm_config_id"))

    if not title or not description:
        raise HTTPException(
            status_code=400, detail="title and description are required"
        )

    # Parse priority
    priority_str = task_data.get("priority", "medium").upper()
    try:
        priority = PriorityEnum[priority_str]
    except KeyError:
        priority = PriorityEnum.MEDIUM

    # Parse domain
    domain = None
    domain_str = task_data.get("domain")
    if domain_str:
        try:
            domain = DomainEnum(domain_str.lower())
        except ValueError:
            pass

    try:
        result = await service.process_task(
            title=title,
            description=description,
            llm_config_id=llm_config_id,
            priority=priority,
            requested_domain=domain,
            input_data=task_data.get("input_data"),
        )

        return {"data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


# Assignment endpoints


@router.get("/tasks/{task_id}/assignments", response_model=dict)
async def get_assignment_recommendations(
    task_id: UUID,
    top_k: int = 3,
    session: AsyncSession = Depends(get_session),
):
    """Get top-k agent recommendations for a task"""
    service = AssignmentService(session)

    recommendations = await service.get_assignment_recommendations(
        task_id=task_id,
        top_k=top_k,
    )

    return {"data": [rec.to_dict() for rec in recommendations]}


@router.post("/tasks/{task_id}/auto-assign", response_model=dict)
async def auto_assign_task(
    task_id: UUID,
    assign_data: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Automatically assign task to best available agent.

    Request body:
    {
        "force": false  // If true, assign even if agent is busy
    }
    """
    service = AssignmentService(session)

    force = assign_data.get("force", False)

    result = await service.auto_assign_task(
        task_id=task_id,
        force=force,
    )

    if not result:
        raise HTTPException(
            status_code=404, detail="No suitable agent found for this task"
        )

    return {
        "data": {
            "assigned": True,
            "agent": result.to_dict(),
        }
    }


@router.get("/agents/{agent_id}/stats", response_model=dict)
async def get_agent_performance_stats(
    agent_id: UUID,
    days: int = 30,
    session: AsyncSession = Depends(get_session),
):
    """Get performance statistics for an agent"""
    service = AssignmentService(session)

    stats = await service.get_agent_stats(
        agent_id=agent_id,
        days=days,
    )

    return {"data": stats}


@router.get("/assignments/rebalance", response_model=dict)
async def get_rebalance_suggestions(
    session: AsyncSession = Depends(get_session),
):
    """Get workload rebalance suggestions (dry run)"""
    service = AssignmentService(session)

    suggestions = await service.rebalance_workload(dry_run=True)

    return {
        "data": {
            "suggestions": suggestions,
            "count": len(suggestions),
        }
    }


@router.post("/assignments/rebalance", response_model=dict)
async def execute_rebalance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Execute workload rebalancing"""
    service = AssignmentService(session)

    changes = await service.rebalance_workload(dry_run=False)

    return {
        "data": {
            "changes": changes,
            "count": len(changes),
        }
    }


# Worker queue endpoints


@router.get("/queue/stats", response_model=dict)
async def get_queue_statistics():
    """Get worker queue statistics"""
    if not WORKER_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Worker queue not available. Redis is required."
        )

    queue = TaskQueue()
    await queue.connect()

    try:
        stats = await queue.get_queue_stats()
        return {"data": stats}
    finally:
        await queue.disconnect()
