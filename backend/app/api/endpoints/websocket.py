"""
WebSocket Endpoints - Real-time communication
"""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ...core.realtime import (
    EventType,
    RealtimeEvent,
    get_connection_manager,
)
from ...core.security import decode_token

router = APIRouter()

# WebSocket close codes
_WS_UNAUTHORIZED = 4001


async def _validate_ws_token(websocket: WebSocket, token: str | None) -> bool:
    """
    Validate a JWT token supplied via WebSocket query param.

    Returns True if valid (or no token provided — open in dev).
    Closes the WebSocket and returns False if the token is invalid.
    """
    if not token:
        return True  # unauthenticated connections allowed (dev / public dashboards)

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=_WS_UNAUTHORIZED, reason="Invalid or expired token")
        return False

    return True


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    """
    WebSocket endpoint for real-time updates.

    Query params:
    - token: Optional JWT access token for authenticated connections

    Events sent to client:
    - task.created, task.updated, task.completed, task.failed
    - agent.status_changed, agent.created
    - tool.executed
    - activity.log
    - metrics.updated
    - system.notification

    Client can subscribe to specific events by sending:
    {"action": "subscribe", "events": ["task.updated", "agent.status_changed"]}
    """
    if not await _validate_ws_token(websocket, token):
        return

    manager = get_connection_manager()

    # Accept connection
    await manager.connect(websocket)

    # Track subscribed events
    subscribed_events: set = set()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            action = data.get("action")

            if action == "subscribe":
                # Subscribe to specific events
                events = data.get("events", [])
                subscribed_events.update(events)

                await manager.send_personal_message(
                    {
                        "type": "subscription.updated",
                        "payload": {"subscribed_to": list(subscribed_events)},
                    },
                    websocket,
                )

            elif action == "unsubscribe":
                # Unsubscribe from events
                events = data.get("events", [])
                for event in events:
                    subscribed_events.discard(event)

                await manager.send_personal_message(
                    {
                        "type": "subscription.updated",
                        "payload": {"subscribed_to": list(subscribed_events)},
                    },
                    websocket,
                )

            elif action == "ping":
                # Health check
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "payload": {
                            "timestamp": RealtimeEvent.create(
                                EventType.ACTIVITY_LOG, {}
                            ).timestamp
                        },
                    },
                    websocket,
                )

            elif action == "get_metrics":
                # Request current metrics
                from ...core.realtime import broadcast_metrics
                from ...database import AsyncSessionLocal

                async with AsyncSessionLocal() as db:
                    await broadcast_metrics(db)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        # Log error and disconnect
        import logging

        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/agents/{agent_id}")
async def agent_websocket(
    websocket: WebSocket,
    agent_id: str,
    token: str | None = Query(None),
):
    """
    WebSocket endpoint for specific agent updates.

    Only receives events related to the specified agent.
    """
    if not await _validate_ws_token(websocket, token):
        return

    manager = get_connection_manager()
    await manager.connect(websocket)

    # Create listener for agent-specific events
    async def agent_listener(event: RealtimeEvent):
        payload = event.payload or {}
        event_agent_id = payload.get("agent_id")

        if event_agent_id == agent_id:
            await manager.send_personal_message(event.to_dict(), websocket)

    # Subscribe to relevant events
    for event_type in [EventType.AGENT_STATUS_CHANGED, EventType.TOOL_EXECUTED]:
        manager.add_listener(event_type, agent_listener)

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup
        for event_type in [EventType.AGENT_STATUS_CHANGED, EventType.TOOL_EXECUTED]:
            manager.remove_listener(event_type, agent_listener)
        manager.disconnect(websocket)


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(
    websocket: WebSocket,
    task_id: str,
    token: str | None = Query(None),
):
    """
    WebSocket endpoint for specific task updates.

    Only receives events related to the specified task.
    """
    if not await _validate_ws_token(websocket, token):
        return

    manager = get_connection_manager()
    await manager.connect(websocket)

    # Create listener for task-specific events
    async def task_listener(event: RealtimeEvent):
        payload = event.payload or {}
        event_task_id = payload.get("task_id")

        if event_task_id == task_id:
            await manager.send_personal_message(event.to_dict(), websocket)

    # Subscribe to relevant events
    for event_type in [
        EventType.TASK_UPDATED,
        EventType.TASK_COMPLETED,
        EventType.TASK_FAILED,
        EventType.TOOL_EXECUTED,
        EventType.ACTIVITY_LOG,
    ]:
        manager.add_listener(event_type, task_listener)

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup
        for event_type in [
            EventType.TASK_UPDATED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
            EventType.TOOL_EXECUTED,
            EventType.ACTIVITY_LOG,
        ]:
            manager.remove_listener(event_type, task_listener)
        manager.disconnect(websocket)
