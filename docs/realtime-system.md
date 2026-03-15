# Qubot — Real-Time System

> **Module**: `backend/app/realtime/`
> **WebSocket endpoint**: `backend/app/routers/websocket.py`
> **Redis**: pub/sub for multi-instance broadcasting

---

## 1. Architecture Overview

```
qubot-worker (or qubot-api action handler)
    │
    │  await redis.publish("ws:global", json_event)
    │  await redis.publish("ws:kanban", json_event)
    │  await redis.publish("ws:agent:{id}", json_event)
    │  await redis.publish("ws:task:{id}", json_event)
    ▼
Redis Pub/Sub
    │
    │  (all qubot-api instances subscribe to "ws:*")
    ▼
ConnectionManager (per qubot-api instance)
    │  background task: listen_redis()
    │
    ├──▶ Forward "ws:global" → all connected clients
    ├──▶ Forward "ws:kanban" → clients subscribed to kanban channel
    ├──▶ Forward "ws:agent:{id}" → clients subscribed to that agent
    └──▶ Forward "ws:task:{id}" → clients subscribed to that task
```

**Why Redis pub/sub for WebSocket?**
- Horizontal scalability: multiple `qubot-api` instances can run, each with their own WebSocket connections. Redis ensures all instances receive all events and forward to their clients.
- Decoupling: the worker process doesn't need to know about WebSocket connections — it just publishes to Redis.

---

## 2. Connection Manager

```python
# backend/app/realtime/manager.py
import json
import asyncio
from collections import defaultdict
from fastapi import WebSocket
from redis.asyncio import Redis
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """
    Manages all active WebSocket connections.
    Routes incoming Redis pub/sub events to subscribed clients.
    """

    def __init__(self):
        # client_id → list of WebSocket connections
        self.connections: dict[str, list[WebSocket]] = defaultdict(list)

        # channel → set of client_ids subscribed to it
        # Channels: "global", "kanban", "agent:{id}", "task:{id}"
        self.subscriptions: dict[str, set[str]] = defaultdict(set)

        self.redis: Redis = None
        self._listen_task: asyncio.Task = None

    async def startup(self, redis: Redis):
        """Called on FastAPI startup. Begin listening to Redis."""
        self.redis = redis
        self._listen_task = asyncio.create_task(self._listen_redis())
        logger.info("connection_manager_started")

    async def shutdown(self):
        """Called on FastAPI shutdown."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.connections[client_id].append(websocket)
        # Auto-subscribe to global channel (everyone gets global events)
        self.subscriptions["global"].add(client_id)
        logger.info("websocket_connected", client_id=client_id)

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove a WebSocket connection and clean up subscriptions."""
        if client_id in self.connections:
            try:
                self.connections[client_id].remove(websocket)
            except ValueError:
                pass
            if not self.connections[client_id]:
                del self.connections[client_id]
                # Remove from all subscriptions
                for channel_subs in self.subscriptions.values():
                    channel_subs.discard(client_id)
        logger.info("websocket_disconnected", client_id=client_id)

    def subscribe(self, client_id: str, channel: str):
        """Subscribe a client to a specific channel."""
        self.subscriptions[channel].add(client_id)

    def unsubscribe(self, client_id: str, channel: str):
        """Unsubscribe a client from a channel."""
        self.subscriptions[channel].discard(client_id)

    async def send_to_client(self, client_id: str, message: dict):
        """Send a message to all WebSocket connections of a client."""
        if client_id not in self.connections:
            return
        dead_sockets = []
        for ws in self.connections[client_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.append(ws)
        # Clean up dead connections
        for ws in dead_sockets:
            await self.disconnect(ws, client_id)

    async def broadcast_to_channel(self, channel: str, message: dict):
        """
        Broadcast to all clients subscribed to a channel.
        Goes through Redis to ensure all API instances receive it.
        """
        await self.redis.publish(f"ws:{channel}", json.dumps(message))

    async def _listen_redis(self):
        """
        Background task: subscribe to Redis pub/sub and forward messages
        to connected WebSocket clients.
        """
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("ws:*")  # Pattern subscribe to all ws:* channels

        logger.info("redis_pubsub_listening", pattern="ws:*")

        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue

            try:
                channel_key = message["channel"].decode()
                # channel_key is like "ws:global", "ws:kanban", "ws:agent:uuid"
                channel_name = channel_key.removeprefix("ws:")

                data = json.loads(message["data"])

                # Find all clients subscribed to this channel
                subscribers = self.subscriptions.get(channel_name, set()).copy()

                # Also send to all clients for "global" channel
                if channel_name == "global":
                    subscribers = set(self.connections.keys())
                elif channel_name == "kanban":
                    subscribers = self.subscriptions.get("kanban", set()).copy()

                for client_id in subscribers:
                    asyncio.create_task(self.send_to_client(client_id, data))

            except Exception as e:
                logger.error("redis_message_processing_error", error=str(e))


# Singleton — initialized at app startup
manager = ConnectionManager()
```

---

## 3. WebSocket Endpoint

```python
# backend/app/routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..core.security import decode_jwt_token
from ..realtime.manager import manager
import json
import uuid

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)  # JWT token passed as query param
):
    """
    Main WebSocket endpoint.

    Client sends JSON messages to subscribe/unsubscribe from channels.
    Server sends real-time events to subscribed clients.

    Authentication: JWT token required as query param ?token=...
    """

    # Authenticate
    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("sub", str(uuid.uuid4()))
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    client_id = str(user_id)

    await manager.connect(websocket, client_id)

    try:
        # Send connected confirmation
        await websocket.send_json({
            "type": "connected",
            "payload": {"client_id": client_id, "message": "WebSocket connected"}
        })

        while True:
            # Receive client messages (subscription management)
            data = await websocket.receive_text()

            try:
                msg = json.loads(data)
                action = msg.get("action")
                channel = msg.get("channel")

                if action == "subscribe":
                    if channel == "agent" and "agent_id" in msg:
                        manager.subscribe(client_id, f"agent:{msg['agent_id']}")
                        await websocket.send_json({
                            "type": "subscribed",
                            "payload": {"channel": f"agent:{msg['agent_id']}"}
                        })

                    elif channel == "task" and "task_id" in msg:
                        manager.subscribe(client_id, f"task:{msg['task_id']}")
                        await websocket.send_json({
                            "type": "subscribed",
                            "payload": {"channel": f"task:{msg['task_id']}"}
                        })

                    elif channel == "kanban":
                        manager.subscribe(client_id, "kanban")
                        await websocket.send_json({
                            "type": "subscribed",
                            "payload": {"channel": "kanban"}
                        })

                    elif channel == "global":
                        # Already auto-subscribed on connect
                        await websocket.send_json({
                            "type": "subscribed",
                            "payload": {"channel": "global"}
                        })

                elif action == "unsubscribe" and channel:
                    manager.unsubscribe(client_id, channel)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "payload": {"channel": channel}
                    })

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket, client_id)
```

---

## 4. Event Broadcasting Helpers

```python
# backend/app/realtime/events.py
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from .manager import manager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def broadcast_agent_status(
    agent_id: UUID,
    agent_name: str,
    old_status: str,
    new_status: str,
    current_task_id: Optional[UUID] = None,
    current_task_title: Optional[str] = None,
):
    """Broadcast agent status change to kanban + agent-specific channel."""
    event = {
        "type": "agent_status_changed",
        "channel": f"agent:{agent_id}",
        "payload": {
            "agent_id": str(agent_id),
            "agent_name": agent_name,
            "old_status": old_status,
            "new_status": new_status,
            "current_task_id": str(current_task_id) if current_task_id else None,
            "current_task_title": current_task_title,
        },
        "timestamp": _now()
    }
    await manager.broadcast_to_channel(f"agent:{agent_id}", event)
    # Also send to kanban (for agent status panel)
    await manager.broadcast_to_channel("kanban", event)


async def broadcast_task_status(
    task_id: UUID,
    task_title: str,
    old_status: str,
    new_status: str,
    assigned_agent_id: Optional[UUID] = None,
    assigned_agent_name: Optional[str] = None,
):
    """Broadcast task Kanban column change."""
    event = {
        "type": "task_status_changed",
        "channel": "kanban",
        "payload": {
            "task_id": str(task_id),
            "task_title": task_title,
            "old_status": old_status,
            "new_status": new_status,
            "assigned_agent_id": str(assigned_agent_id) if assigned_agent_id else None,
            "assigned_agent_name": assigned_agent_name,
        },
        "timestamp": _now()
    }
    await manager.broadcast_to_channel("kanban", event)
    await manager.broadcast_to_channel(f"task:{task_id}", event)


async def broadcast_task_event(
    task_id: UUID,
    event_type: str,
    payload: dict,
    agent_id: Optional[UUID] = None,
    agent_name: Optional[str] = None,
):
    """Broadcast a new TaskEvent (tool call, progress update, etc.)."""
    event = {
        "type": "task_event_created",
        "channel": f"task:{task_id}",
        "payload": {
            "task_id": str(task_id),
            "event_type": event_type,
            "payload": payload,
            "agent_id": str(agent_id) if agent_id else None,
            "agent_name": agent_name,
        },
        "timestamp": _now()
    }
    await manager.broadcast_to_channel(f"task:{task_id}", event)


async def broadcast_activity(
    message: str,
    severity: str = "info",
    agent_id: Optional[UUID] = None,
    agent_name: Optional[str] = None,
    agent_domain: Optional[str] = None,
    task_id: Optional[UUID] = None,
    task_title: Optional[str] = None,
):
    """Broadcast to global activity feed."""
    event = {
        "type": "activity_feed",
        "channel": "global",
        "payload": {
            "message": message,
            "severity": severity,
            "agent_id": str(agent_id) if agent_id else None,
            "agent_name": agent_name,
            "agent_domain": agent_domain,
            "task_id": str(task_id) if task_id else None,
            "task_title": task_title,
        },
        "timestamp": _now()
    }
    await manager.broadcast_to_channel("global", event)


async def broadcast_agent_heartbeat(agent_id: UUID, status: str, iteration: int = 0):
    """Periodic heartbeat — sent every 30s by worker for active agents."""
    event = {
        "type": "agent_heartbeat",
        "channel": f"agent:{agent_id}",
        "payload": {
            "agent_id": str(agent_id),
            "status": status,
            "iteration": iteration,
        },
        "timestamp": _now()
    }
    await manager.broadcast_to_channel(f"agent:{agent_id}", event)
```

---

## 5. FastAPI App Startup/Shutdown

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .realtime.manager import manager
from .redis_client import get_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis = await get_redis()
    await manager.startup(redis)
    yield
    # Shutdown
    await manager.shutdown()

app = FastAPI(lifespan=lifespan)
```

---

## 6. Redis Client

```python
# backend/app/redis_client.py
import redis.asyncio as redis
from .config import settings

_redis_client = None

async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        await _redis_client.ping()
    return _redis_client

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
```

---

## 7. Channels Reference

| Channel | Who publishes | Who subscribes | Events |
|---------|--------------|----------------|--------|
| `global` | Worker, orchestrator | All clients (auto) | `activity_feed` |
| `kanban` | Worker, orchestrator, API | Clients subscribed to kanban | `task_status_changed`, `agent_status_changed` |
| `agent:{id}` | Worker | Clients watching that agent | `agent_status_changed`, `agent_heartbeat` |
| `task:{id}` | Worker, API | Clients watching that task | `task_event_created`, `task_status_changed` |

---

## 8. Frontend WebSocket Client

```typescript
// frontend/lib/websocket.ts
import { io, Socket } from "socket.io-client";

// NOTE: Using native WebSocket API (not Socket.io)
// Socket.io is NOT used — plain WebSocket for simplicity

let ws: WebSocket | null = null;
const listeners: Map<string, ((event: any) => void)[]> = new Map();

export function connect(token: string): WebSocket {
  if (ws && ws.readyState === WebSocket.OPEN) return ws;

  const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws?token=${token}`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("WebSocket connected");
    // Auto-subscribe to kanban and global
    subscribe("kanban");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      const handlers = listeners.get(data.type) || [];
      handlers.forEach(handler => handler(data));

      // Also fire wildcard listeners
      const wildcardHandlers = listeners.get("*") || [];
      wildcardHandlers.forEach(handler => handler(data));
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };

  ws.onclose = () => {
    console.log("WebSocket disconnected, reconnecting in 3s...");
    setTimeout(() => connect(token), 3000);
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  return ws;
}

export function subscribe(channel: string, agentId?: string, taskId?: string) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const msg: any = { action: "subscribe", channel };
  if (agentId) msg.agent_id = agentId;
  if (taskId) msg.task_id = taskId;
  ws.send(JSON.stringify(msg));
}

export function on(eventType: string, handler: (event: any) => void) {
  if (!listeners.has(eventType)) listeners.set(eventType, []);
  listeners.get(eventType)!.push(handler);
}

export function off(eventType: string, handler: (event: any) => void) {
  const handlers = listeners.get(eventType) || [];
  const idx = handlers.indexOf(handler);
  if (idx > -1) handlers.splice(idx, 1);
}

export function send(message: object) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  }
}
```

---

## 9. useWebSocket React Hook

```typescript
// frontend/hooks/useWebSocket.ts
import { useEffect, useCallback } from "react";
import * as wsClient from "@/lib/websocket";
import { useActivityStore } from "@/store/activity.store";
import { useAgentsStore } from "@/store/agents.store";
import { useTasksStore } from "@/store/tasks.store";

export function useWebSocket(token: string | null) {
  const addActivity = useActivityStore(s => s.addEntry);
  const updateAgentStatus = useAgentsStore(s => s.updateStatus);
  const updateTaskStatus = useTasksStore(s => s.updateStatus);

  useEffect(() => {
    if (!token) return;
    wsClient.connect(token);

    // Activity feed
    const onActivity = (event: any) => {
      addActivity(event.payload);
    };

    // Agent status changes
    const onAgentStatus = (event: any) => {
      updateAgentStatus(event.payload.agent_id, event.payload.new_status, {
        currentTaskId: event.payload.current_task_id,
        currentTaskTitle: event.payload.current_task_title,
      });
    };

    // Kanban updates
    const onTaskStatus = (event: any) => {
      updateTaskStatus(event.payload.task_id, event.payload.new_status, {
        assignedAgentId: event.payload.assigned_agent_id,
        assignedAgentName: event.payload.assigned_agent_name,
      });
    };

    wsClient.on("activity_feed", onActivity);
    wsClient.on("agent_status_changed", onAgentStatus);
    wsClient.on("task_status_changed", onTaskStatus);

    return () => {
      wsClient.off("activity_feed", onActivity);
      wsClient.off("agent_status_changed", onAgentStatus);
      wsClient.off("task_status_changed", onTaskStatus);
    };
  }, [token, addActivity, updateAgentStatus, updateTaskStatus]);
}

export function useAgentWebSocket(agentId: string) {
  useEffect(() => {
    wsClient.subscribe("agent", agentId);
  }, [agentId]);
}

export function useTaskWebSocket(taskId: string) {
  useEffect(() => {
    wsClient.subscribe("task", undefined, taskId);
  }, [taskId]);
}
```

---

## 10. Activity Feed Store

```typescript
// frontend/store/activity.store.ts
import { create } from "zustand";

export interface ActivityEntry {
  id: string;
  message: string;
  severity: "info" | "warning" | "error" | "success";
  agent_id?: string;
  agent_name?: string;
  agent_domain?: string;
  task_id?: string;
  task_title?: string;
  timestamp: string;
}

interface ActivityState {
  entries: ActivityEntry[];
  addEntry: (entry: Omit<ActivityEntry, "id">) => void;
  clear: () => void;
}

export const useActivityStore = create<ActivityState>((set) => ({
  entries: [],
  addEntry: (entry) =>
    set((state) => ({
      entries: [
        { ...entry, id: crypto.randomUUID() },
        ...state.entries.slice(0, 199), // Keep last 200 entries
      ],
    })),
  clear: () => set({ entries: [] }),
}));
```
