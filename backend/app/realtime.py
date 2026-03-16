"""
Qubot Real-time WebSocket Manager
----------------------------------
Module-level singleton – import `manager` or the broadcast helpers everywhere.
"""

import json
import logging
import uuid
from datetime import datetime

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("[WS] Client connected  — total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "[WS] Client disconnected — total: %d", len(self.active_connections)
        )

    async def broadcast(self, data: dict):
        if not self.active_connections:
            return
        message = json.dumps(data, default=str)
        dead: list[WebSocket] = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to(self, websocket: WebSocket, data: dict):
        """Send a message to a single client only."""
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except Exception as exc:
            logger.warning("[WS] send_to failed: %s", exc)
            self.disconnect(websocket)


# ── Singleton ─────────────────────────────────────────────────────────────────
manager = ConnectionManager()


# ── Broadcast helpers ─────────────────────────────────────────────────────────


async def broadcast_agent_update(agent_id: int, payload: dict):
    await manager.broadcast(
        {
            "type": "AGENT_UPDATE",
            "id": agent_id,
            "payload": payload,
        }
    )


async def broadcast_task_update(task_id: int, payload: dict):
    await manager.broadcast(
        {
            "type": "TASK_UPDATE",
            "id": task_id,
            "payload": payload,
        }
    )


async def broadcast_activity(status: str, agent_name: str, message: str):
    await manager.broadcast(
        {
            "type": "ACTIVITY_EVENT",
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            "status": status,
            "agentName": agent_name,
            "message": message,
        }
    )


async def broadcast_metrics(
    db_session=None,
    *,
    active_tasks: int = 0,
    total_tokens: int = 0,
    total_cost: float = 0.0,
    today_cost: float = 0.0,
):
    """Broadcast current system metrics. Pass db_session to auto-compute active_tasks."""
    if db_session is not None:
        try:
            from .models.database import Task
            from .models.enums import TaskStatusEnum

            active_tasks = (
                db_session.query(Task)
                .filter(
                    Task.status.in_(
                        [TaskStatusEnum.PLANNING, TaskStatusEnum.IN_PROGRESS]
                    )
                )
                .count()
            )
        except Exception:
            pass

    await manager.broadcast(
        {
            "type": "METRICS_UPDATE",
            "payload": {
                "activeTasks": active_tasks,
                "totalTokens": total_tokens,
                "totalCost": total_cost,
                "todayCost": today_cost,
            },
        }
    )
