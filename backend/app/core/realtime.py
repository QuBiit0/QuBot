"""
Real-time Communication System - WebSocket + Redis Pub/Sub

Provides scalable real-time updates using Redis pub/sub for multi-instance deployments.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..config import settings

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of real-time events"""

    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_ASSIGNED = "task.assigned"

    # Agent events
    AGENT_STATUS_CHANGED = "agent.status_changed"
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"

    # Tool events
    TOOL_EXECUTED = "tool.executed"

    # System events
    SYSTEM_NOTIFICATION = "system.notification"
    METRICS_UPDATED = "metrics.updated"

    # Activity events
    ACTIVITY_LOG = "activity.log"


@dataclass
class RealtimeEvent:
    """Real-time event structure"""

    type: EventType
    payload: dict[str, Any]
    timestamp: str
    sender_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "sender_id": self.sender_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def create(
        cls,
        event_type: EventType,
        payload: dict[str, Any],
        sender_id: str | None = None,
    ) -> "RealtimeEvent":
        return cls(
            type=event_type,
            payload=payload,
            timestamp=datetime.utcnow().isoformat(),
            sender_id=sender_id,
        )


class ConnectionManager:
    """
    Manages WebSocket connections with Redis pub/sub for scalability.

    In a single-instance setup, broadcasts directly to connected clients.
    In a multi-instance setup, uses Redis pub/sub to broadcast across instances.
    """

    def __init__(self):
        self.active_connections: set[Any] = set()
        self.redis_client: Any | None = None
        self.redis_pubsub: Any | None = None
        self._pubsub_task: asyncio.Task | None = None
        self._listeners: dict[EventType, set[Callable]] = {}
        self._instance_id = f"instance_{datetime.utcnow().timestamp()}"

    async def connect(self, websocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

        # Send initial connection success
        await self.send_personal_message(
            {
                "type": "connection.established",
                "payload": {"client_id": str(id(websocket))},
            },
            websocket,
        )

    def disconnect(self, websocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast to all connected clients on this instance"""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def setup_redis(self):
        """Setup Redis pub/sub for cross-instance communication"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, running in single-instance mode")
            return

        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_pubsub = self.redis_client.pubsub()

            # Subscribe to broadcast channel
            await self.redis_pubsub.subscribe("qubot:broadcast")

            # Start listener task
            self._pubsub_task = asyncio.create_task(self._redis_listener())

            logger.info("Redis pub/sub connected")
        except Exception as e:
            logger.error(f"Failed to setup Redis: {e}")
            self.redis_client = None
            self.redis_pubsub = None

    async def _redis_listener(self):
        """Listen for messages from Redis pub/sub"""
        if not self.redis_pubsub:
            return

        try:
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    # Broadcast to local clients
                    data = json.loads(message["data"])
                    await self.broadcast(data)
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def publish_event(self, event: RealtimeEvent):
        """
        Publish event to all clients (local and remote).

        If Redis is available, publishes to Redis channel.
        Otherwise, broadcasts only to local clients.
        """
        message = event.to_dict()

        # Broadcast locally first
        await self.broadcast(message)

        # Publish to Redis for other instances
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "qubot:broadcast",
                    json.dumps(message, default=str),
                )
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

        # Notify local listeners
        await self._notify_listeners(event)

    def add_listener(self, event_type: EventType, callback: Callable):
        """Add event listener for specific event type"""
        if event_type not in self._listeners:
            self._listeners[event_type] = set()
        self._listeners[event_type].add(callback)

    def remove_listener(self, event_type: EventType, callback: Callable):
        """Remove event listener"""
        if event_type in self._listeners:
            self._listeners[event_type].discard(callback)

    async def _notify_listeners(self, event: RealtimeEvent):
        """Notify registered listeners"""
        callbacks = self._listeners.get(event.type, set())
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Listener error: {e}")

    async def close(self):
        """Cleanup resources"""
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass

        if self.redis_pubsub:
            await self.redis_pubsub.unsubscribe("qubot:broadcast")
            await self.redis_pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Connection manager closed")


# Global connection manager instance
_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get or create global connection manager"""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


class NotificationService:
    """Service for sending notifications to users/agents"""

    def __init__(self):
        self.manager = get_connection_manager()

    async def notify_task_update(
        self,
        task_id: UUID,
        status: str,
        agent_id: UUID | None = None,
        message: str | None = None,
    ):
        """Send task update notification"""
        event_type = {
            "completed": EventType.TASK_COMPLETED,
            "failed": EventType.TASK_FAILED,
            "assigned": EventType.TASK_ASSIGNED,
        }.get(status, EventType.TASK_UPDATED)

        event = RealtimeEvent.create(
            event_type=event_type,
            payload={
                "task_id": str(task_id),
                "status": status,
                "agent_id": str(agent_id) if agent_id else None,
                "message": message,
            },
        )

        await self.manager.publish_event(event)

    async def notify_agent_status(
        self,
        agent_id: UUID,
        status: str,
        current_task_id: UUID | None = None,
    ):
        """Send agent status change notification"""
        event = RealtimeEvent.create(
            event_type=EventType.AGENT_STATUS_CHANGED,
            payload={
                "agent_id": str(agent_id),
                "status": status,
                "current_task_id": str(current_task_id) if current_task_id else None,
            },
        )

        await self.manager.publish_event(event)

    async def notify_tool_execution(
        self,
        task_id: UUID,
        tool_name: str,
        success: bool,
        execution_time_ms: int,
    ):
        """Send tool execution notification"""
        event = RealtimeEvent.create(
            event_type=EventType.TOOL_EXECUTED,
            payload={
                "task_id": str(task_id),
                "tool_name": tool_name,
                "success": success,
                "execution_time_ms": execution_time_ms,
            },
        )

        await self.manager.publish_event(event)

    async def log_activity(
        self,
        activity_type: str,
        description: str,
        agent_id: UUID | None = None,
        task_id: UUID | None = None,
        metadata: dict | None = None,
    ):
        """Log and broadcast activity"""
        event = RealtimeEvent.create(
            event_type=EventType.ACTIVITY_LOG,
            payload={
                "type": activity_type,
                "description": description,
                "agent_id": str(agent_id) if agent_id else None,
                "task_id": str(task_id) if task_id else None,
                "metadata": metadata or {},
            },
        )

        await self.manager.publish_event(event)

    async def send_system_notification(
        self,
        title: str,
        message: str,
        level: str = "info",  # info, warning, error, success
    ):
        """Send system-wide notification"""
        event = RealtimeEvent.create(
            event_type=EventType.SYSTEM_NOTIFICATION,
            payload={
                "title": title,
                "message": message,
                "level": level,
            },
        )

        await self.manager.publish_event(event)


# Legacy support for existing code
class LegacyRealtimeManager:
    """Legacy wrapper for backwards compatibility"""

    def __init__(self):
        self.manager = get_connection_manager()
        self.notification = NotificationService()

    async def connect(self, websocket):
        await self.manager.connect(websocket)

    def disconnect(self, websocket):
        self.manager.disconnect(websocket)

    async def broadcast(self, message: dict):
        await self.manager.broadcast(message)


# Create legacy manager instance for existing code
manager = LegacyRealtimeManager()


# Helper function for metrics broadcasting (legacy support)
async def broadcast_metrics(db):
    """Broadcast metrics to all connected clients"""
    from sqlalchemy import func, select

    from ..models.agent import Agent
    from ..models.enums import AgentStatusEnum, TaskStatusEnum
    from ..models.task import Task

    # Get counts
    total_tasks = await db.scalar(select(func.count(Task.id)))
    completed_tasks = await db.scalar(
        select(func.count(Task.id)).where(Task.status == TaskStatusEnum.DONE)
    )
    active_tasks = await db.scalar(
        select(func.count(Task.id)).where(Task.status == TaskStatusEnum.IN_PROGRESS)
    )

    total_agents = await db.scalar(select(func.count(Agent.id)))
    active_agents = await db.scalar(
        select(func.count(Agent.id)).where(Agent.status == AgentStatusEnum.WORKING)
    )

    event = RealtimeEvent.create(
        event_type=EventType.METRICS_UPDATED,
        payload={
            "tasks": {
                "total": total_tasks or 0,
                "completed": completed_tasks or 0,
                "active": active_tasks or 0,
            },
            "agents": {
                "total": total_agents or 0,
                "active": active_agents or 0,
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    await manager.broadcast(event.to_dict())


# Legacy broadcast_activity function for backwards compatibility
async def broadcast_activity(
    status: str,
    agent_name: str,
    message: str,
    metadata: dict[str, Any] | None = None,
):
    """
    Broadcast activity log event.

    Legacy support for existing code using the old API.
    """
    notification = NotificationService()
    await notification.log_activity(
        activity_type=status,
        description=message,
        metadata={
            "agent_name": agent_name,
            **(metadata or {}),
        },
    )
