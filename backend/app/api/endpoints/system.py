"""
System API Endpoints - Health checks, metrics, and system info
"""

import platform
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ...core.metrics import CONTENT_TYPE_LATEST
from ...core.metrics import get_metrics as _get_metrics
from ...database import get_session

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

router = APIRouter()

# Track startup time
STARTUP_TIME = time.time()


@router.get("/health", response_model=dict)
async def health_check(
    session: AsyncSession = Depends(get_session),
):
    """
    Health check endpoint.

    Returns 200 if all services are healthy.
    Returns 503 if any service is unhealthy.
    """
    checks = {
        "api": await _check_api(),
        "database": await _check_database(session),
    }

    # Optional Redis check
    if REDIS_AVAILABLE:
        checks["redis"] = await _check_redis()

    # Determine overall health
    all_healthy = all(check["status"] == "healthy" for check in checks.values())

    response = {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - STARTUP_TIME),
        "checks": checks,
    }

    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response,
        )

    return response


@router.get("/health/ready", response_model=dict)
async def readiness_check(
    session: AsyncSession = Depends(get_session),
):
    """
    Kubernetes readiness probe.

    Returns 200 when the application is ready to receive traffic.
    """
    # Check database connectivity
    db_check = await _check_database(session)

    if db_check["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ready": False, "reason": "Database connection failed"},
        )

    return {"ready": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/live", response_model=dict)
async def liveness_check():
    """
    Kubernetes liveness probe.

    Returns 200 if the application is running.
    If this fails, Kubernetes will restart the pod.
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics", response_model=dict)
async def get_metrics(
    session: AsyncSession = Depends(get_session),
):
    """
    System metrics endpoint.

    Returns current metrics about the system state.
    """
    from sqlalchemy import func

    from ...models.agent import Agent
    from ...models.enums import AgentStatusEnum, TaskStatusEnum
    from ...models.task import Task

    # Task metrics
    task_stats = await session.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status)
    )
    task_counts = {status.value: count for status, count in task_stats.all()}

    total_tasks = sum(task_counts.values())
    completed_tasks = task_counts.get(TaskStatusEnum.DONE.value, 0)
    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Agent metrics
    agent_stats = await session.execute(
        select(Agent.status, func.count(Agent.id)).group_by(Agent.status)
    )
    agent_counts = {status.value: count for status, count in agent_stats.all()}

    # Recent activity
    from ...models.task import TaskEvent

    recent_events = await session.execute(
        select(TaskEvent).order_by(TaskEvent.created_at.desc()).limit(10)
    )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "tasks": {
            "total": total_tasks,
            "by_status": task_counts,
            "completion_rate": round(success_rate, 2),
        },
        "agents": {
            "total": sum(agent_counts.values()),
            "by_status": agent_counts,
            "active": agent_counts.get(AgentStatusEnum.WORKING.value, 0),
        },
        "recent_events": [
            {
                "type": event.type.value,
                "task_id": str(event.task_id),
                "created_at": event.created_at.isoformat(),
            }
            for event in recent_events.scalars().all()
        ],
    }


@router.get("/info", response_model=dict)
async def get_system_info():
    """
    System information endpoint.

    Returns version and configuration info.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": "production" if not settings.DEBUG else "development",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "features": {
            "redis": REDIS_AVAILABLE,
            "debug": settings.DEBUG,
        },
    }


@router.get("/config", response_model=dict)
async def get_public_config():
    """
    Public configuration endpoint.

    Returns non-sensitive configuration values.
    """
    return {
        "project_name": settings.PROJECT_NAME,
        "api_version": "v1",
        "features": {
            "websocket": True,
            "redis_pubsub": REDIS_AVAILABLE,
        },
        "limits": {
            "max_task_iterations": 10,
            "max_tool_execution_time": 300,
        },
    }


async def _check_api() -> dict[str, Any]:
    """Check API health"""
    return {
        "status": "healthy",
        "message": "API is running",
    }


async def _check_database(session: AsyncSession) -> dict[str, Any]:
    """Check database connectivity"""
    try:
        # Execute simple query
        await session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "message": "Database connection OK",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }


async def _check_redis() -> dict[str, Any]:
    """Check Redis connectivity"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        return {
            "status": "healthy",
            "message": "Redis connection OK",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
        }


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus exposition format.
    """
    from fastapi import Response

    return Response(
        content=_get_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
