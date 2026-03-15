# Qubot — API Specification

> **Base URL**: `/api/v1`
> **Auth**: `Authorization: Bearer <jwt_token>` on all endpoints except `/system/health`
> **Content-Type**: `application/json`
> **WebSocket**: `ws://{host}/ws`

---

## 1. Standard Response Envelopes

All REST responses use these standard formats.

### Success (single resource)
```json
{
  "data": { ...resource fields... }
}
```

### Success (paginated list)
```json
{
  "data": [ ...items... ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      { "field": "name", "message": "Field is required" }
    ]
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (invalid input) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate, constraint violation) |
| 422 | Unprocessable Entity (Pydantic validation failure) |
| 500 | Internal Server Error |

---

## 2. Authentication

### POST `/auth/login`

Authenticate and receive JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Response 200:**
```json
{
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### POST `/auth/refresh`

Refresh JWT token.

**Request:** Requires valid token in `Authorization` header.

**Response 200:** Same as login.

---

## 3. Agents

### GET `/agents`

List all agents with current status.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | `IDLE\|WORKING\|ERROR\|OFFLINE` | Filter by status |
| `domain` | `DomainEnum` | Filter by domain |
| `is_orchestrator` | `bool` | Filter orchestrator only |
| `page` | `int` (default: 1) | Page number |
| `limit` | `int` (default: 20, max: 100) | Items per page |

**Response 200:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Sofia",
      "gender": "FEMALE",
      "class_id": "...",
      "class_name": "Finance Manager",
      "domain": "FINANCE",
      "role_description": "Senior finance manager focused on LATAM markets",
      "status": "WORKING",
      "is_orchestrator": false,
      "current_task_id": "abc-123",
      "current_task_title": "Q3 Financial Analysis",
      "avatar_config": {
        "sprite_id": "finance_manager",
        "color_primary": "#D97706",
        "color_secondary": "#44260a",
        "icon": "💰",
        "desk_position": {"x": 3, "y": 1}
      },
      "llm_config_id": "...",
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "meta": { "page": 1, "limit": 20, "total": 8, "total_pages": 1 }
}
```

### POST `/agents`

Create a new agent (from wizard).

**Request:**
```json
{
  "name": "Sofia",
  "gender": "FEMALE",
  "class_id": "uuid-of-agent-class",
  "domain": "FINANCE",
  "role_description": "Senior finance manager focused on LATAM markets",
  "personality": {
    "detail_oriented": 85,
    "risk_tolerance": 25,
    "formality": 80,
    "strengths": ["financial modeling", "risk assessment"],
    "weaknesses": ["ambiguous tasks"],
    "communication_style": "formal and precise"
  },
  "llm_config_id": "uuid-of-llm-config",
  "avatar_config": {
    "sprite_id": "finance_manager",
    "color_primary": "#D97706",
    "color_secondary": "#44260a",
    "icon": "💰",
    "desk_position": {"x": 3, "y": 1}
  },
  "is_orchestrator": false,
  "tool_assignments": [
    { "tool_id": "uuid-of-http-tool", "permissions": "READ_WRITE" },
    { "tool_id": "uuid-of-browser-tool", "permissions": "READ_ONLY" }
  ]
}
```

**Response 201:**
```json
{
  "data": { ...full agent object with id... }
}
```

### GET `/agents/{id}`

Get agent detail including assigned tools and recent tasks.

**Response 200:**
```json
{
  "data": {
    ...agent fields...,
    "tools": [
      {
        "tool_id": "...",
        "tool_name": "HTTP API Tool",
        "tool_type": "HTTP_API",
        "permissions": "READ_WRITE"
      }
    ],
    "recent_tasks": [
      {
        "id": "...",
        "title": "Q3 Analysis",
        "status": "DONE",
        "completed_at": "2025-01-15T12:00:00Z"
      }
    ]
  }
}
```

### PUT `/agents/{id}`

Update agent configuration.

**Request:** Same fields as POST (all optional except must include at least one field).

**Response 200:** Full updated agent object.

### DELETE `/agents/{id}`

Soft delete agent (sets status to OFFLINE, keeps history).

**Response 204:** No content.

### PATCH `/agents/{id}/status`

Manually override agent status (admin action).

**Request:**
```json
{ "status": "OFFLINE" }
```

**Response 200:**
```json
{ "data": { "id": "...", "status": "OFFLINE" } }
```

### GET `/agents/{id}/tasks`

Get agent's task history.

**Query Parameters:** `page`, `limit`, `status` filter.

**Response 200:** Paginated list of tasks assigned to this agent.

### GET `/agents/{id}/memory`

Get agent's memory entries sorted by importance.

**Response 200:**
```json
{
  "data": [
    {
      "id": "...",
      "key": "preferred_format",
      "content": "Always output financial data as markdown tables",
      "importance": 5,
      "last_accessed": "2025-01-15T11:00:00Z"
    }
  ],
  "meta": { ... }
}
```

---

## 4. Agent Classes

### GET `/agent-classes`

List all agent classes.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `domain` | `DomainEnum` | Filter by domain |
| `is_custom` | `bool` | Only predefined or only custom |

**Response 200:**
```json
{
  "data": [
    {
      "id": "...",
      "name": "Finance Manager",
      "description": "Oversees financial operations...",
      "domain": "FINANCE",
      "is_custom": false,
      "default_avatar_config": { ... }
    }
  ]
}
```

### POST `/agent-classes`

Create a custom agent class.

**Request:**
```json
{
  "name": "LATAM Finance Manager",
  "description": "Finance manager specialized in LATAM markets and regulations",
  "domain": "FINANCE",
  "default_avatar_config": {
    "sprite_id": "finance_manager",
    "color_primary": "#10B981",
    "icon": "💱",
    "badge": "LATAM"
  }
}
```

**Response 201:** Full AgentClass object with `is_custom: true`.

### PUT `/agent-classes/{id}`

Update a custom class (predefined classes are read-only, returns 403 if attempted).

### DELETE `/agent-classes/{id}`

Delete a custom class. Returns 409 if agents are using it.

---

## 5. Tasks

### GET `/tasks`

List tasks for Kanban board.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | `TaskStatusEnum` | Filter by Kanban column |
| `priority` | `PriorityEnum` | Filter by priority |
| `domain_hint` | `DomainEnum` | Filter by domain |
| `assigned_agent_id` | `UUID` | Filter by agent |
| `parent_task_id` | `UUID` | Get subtasks of a parent |
| `page` | `int` | Page |
| `limit` | `int` | Per page |

**Response 200:**
```json
{
  "data": [
    {
      "id": "...",
      "title": "Q3 Financial Analysis",
      "description": "Analyze Q3 revenue data...",
      "status": "IN_PROGRESS",
      "priority": "HIGH",
      "domain_hint": "FINANCE",
      "created_by": "user",
      "assigned_agent_id": "...",
      "assigned_agent_name": "Sofia",
      "assigned_agent_avatar": { ... },
      "parent_task_id": null,
      "subtask_count": 2,
      "created_at": "2025-01-15T09:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z",
      "completed_at": null
    }
  ],
  "meta": { ... }
}
```

### POST `/tasks`

Manually create a task (bypasses orchestrator).

**Request:**
```json
{
  "title": "Review Q3 Budget",
  "description": "Review and approve the Q3 budget proposal for the LATAM division",
  "priority": "HIGH",
  "domain_hint": "FINANCE",
  "assigned_agent_id": "uuid-optional"
}
```

**Response 201:** Full task object.

### GET `/tasks/{id}`

Get task detail with full event timeline.

**Response 200:**
```json
{
  "data": {
    ...task fields...,
    "events": [
      {
        "id": "...",
        "type": "CREATED",
        "payload": { "title": "...", "description": "..." },
        "agent_id": null,
        "created_at": "2025-01-15T09:00:00Z"
      },
      {
        "id": "...",
        "type": "ASSIGNED",
        "payload": { "agent_id": "...", "agent_name": "Sofia" },
        "agent_id": "...",
        "created_at": "2025-01-15T09:01:00Z"
      },
      {
        "id": "...",
        "type": "TOOL_CALL",
        "payload": {
          "tool_name": "http_api",
          "input": { "method": "GET", "path": "/financials/q3" },
          "output": { "status_code": 200, "body": { ... } },
          "duration_ms": 342,
          "success": true
        },
        "agent_id": "...",
        "created_at": "2025-01-15T09:02:30Z"
      }
    ],
    "subtasks": [ ...child tasks... ]
  }
}
```

### PUT `/tasks/{id}`

Update task fields.

**Request:**
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "priority": "CRITICAL"
}
```

### PATCH `/tasks/{id}/status`

Move task between Kanban columns (manual drag & drop).

**Request:**
```json
{ "status": "IN_REVIEW" }
```

**Response 200:** Updated task.

### PATCH `/tasks/{id}/assign`

Assign or reassign task to an agent.

**Request:**
```json
{ "agent_id": "uuid-of-agent" }
```

**Response 200:** Updated task. Also emits WebSocket `task_status_changed` event.

### GET `/tasks/{id}/events`

Stream task events as Server-Sent Events (SSE).

**Response:** `text/event-stream` with `data: {...event_json...}\n\n` per event.

### POST `/tasks/{id}/events`

Add a manual comment or annotation to a task.

**Request:**
```json
{
  "type": "COMMENT",
  "payload": { "author": "user", "text": "Please prioritize this task." }
}
```

**Response 201:** Created TaskEvent.

---

## 6. Tools

### GET `/tools`

List all registered tools.

**Query Parameters:** `type` (ToolTypeEnum filter), `page`, `limit`.

**Response 200:**
```json
{
  "data": [
    {
      "id": "...",
      "name": "HTTP API Tool",
      "type": "HTTP_API",
      "description": "Makes HTTP requests to external APIs",
      "is_dangerous": false,
      "config": {
        "base_url": "https://api.example.com",
        "auth_type": "bearer"
      }
    }
  ]
}
```

### POST `/tools`

Register a new tool.

**Request:**
```json
{
  "name": "Finance API",
  "type": "HTTP_API",
  "description": "Accesses the internal finance data API. Use this to retrieve balance sheets, P&L statements, and transaction data.",
  "input_schema": {
    "type": "object",
    "properties": {
      "method": { "type": "string", "enum": ["GET", "POST"] },
      "path": { "type": "string" },
      "body": { "type": "object" }
    },
    "required": ["method", "path"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "status_code": { "type": "integer" },
      "body": {}
    }
  },
  "config": {
    "base_url": "https://internal.finance.company.com",
    "auth_type": "bearer",
    "auth_env_ref": "FINANCE_API_KEY",
    "timeout": 30,
    "allowed_domains": ["internal.finance.company.com"]
  },
  "is_dangerous": false
}
```

**Response 201:** Full tool object.

### GET `/tools/{id}`

Get tool detail.

### PUT `/tools/{id}`

Update tool configuration.

### DELETE `/tools/{id}`

Remove tool. Returns 409 if agents are using it.

### POST `/tools/{id}/test`

Execute the tool with sample input to verify configuration.

**Request:**
```json
{
  "input": {
    "method": "GET",
    "path": "/health"
  }
}
```

**Response 200:**
```json
{
  "data": {
    "success": true,
    "output": { "status_code": 200, "body": { "status": "ok" } },
    "duration_ms": 234,
    "error": null
  }
}
```

---

## 7. LLM Configurations

### GET `/llm-configs`

List all LLM configurations.

**Response 200:**
```json
{
  "data": [
    {
      "id": "...",
      "name": "GPT-4o Production",
      "provider": "OPENAI",
      "model_name": "gpt-4o",
      "temperature": 0.7,
      "top_p": 1.0,
      "max_tokens": 4096,
      "api_key_ref": "OPENAI_API_KEY"
    }
  ]
}
```

Note: `api_key_ref` is returned (the env var name), never the actual key value.

### POST `/llm-configs`

Create a new LLM config.

**Request:**
```json
{
  "name": "Claude Sonnet Fast",
  "provider": "ANTHROPIC",
  "model_name": "claude-sonnet-4-6",
  "temperature": 0.5,
  "top_p": 1.0,
  "max_tokens": 8192,
  "api_key_ref": "ANTHROPIC_API_KEY",
  "extra_config": {}
}
```

**Response 201:** Full LlmConfig object.

### PUT `/llm-configs/{id}`

Update LLM config.

### DELETE `/llm-configs/{id}`

Delete config. Returns 409 if agents are using it.

### POST `/llm-configs/{id}/test`

Test provider connectivity with a minimal request.

**Response 200:**
```json
{
  "data": {
    "success": true,
    "provider": "ANTHROPIC",
    "model": "claude-sonnet-4-6",
    "latency_ms": 892,
    "error": null
  }
}
```

---

## 8. Orchestrator Chat

### POST `/chat`

Send a message to the orchestrator agent. The orchestrator processes it, takes actions, and responds.

**Request:**
```json
{
  "message": "Analyze our Q3 financial performance and prepare a summary report",
  "context": {}
}
```

**Response 200:**
```json
{
  "data": {
    "response": "I'll assign this to Sofia, our Finance Manager. She'll analyze the Q3 data and prepare the report.",
    "actions_taken": [
      {
        "type": "CREATE_TASK",
        "result": {
          "task_id": "...",
          "title": "Q3 Financial Performance Analysis",
          "priority": "HIGH"
        }
      },
      {
        "type": "ASSIGN_TASK",
        "result": {
          "task_id": "...",
          "agent_id": "...",
          "agent_name": "Sofia"
        }
      }
    ],
    "timestamp": "2025-01-15T10:00:00Z"
  }
}
```

### GET `/chat/history`

Get recent conversation history between user and orchestrator.

**Query Parameters:** `page`, `limit`.

**Response 200:**
```json
{
  "data": [
    {
      "id": "...",
      "role": "user",
      "content": "Analyze our Q3 financial performance...",
      "timestamp": "2025-01-15T10:00:00Z"
    },
    {
      "id": "...",
      "role": "assistant",
      "content": "I'll assign this to Sofia...",
      "actions_taken": [...],
      "timestamp": "2025-01-15T10:00:02Z"
    }
  ]
}
```

---

## 9. Memory

### GET `/memory/global`

List global memory entries.

**Query Parameters:** `tags` (comma-separated), `page`, `limit`.

**Response 200:**
```json
{
  "data": [
    {
      "id": "...",
      "key": "company_overview",
      "content": "# Company Overview\n\nOur company operates in...",
      "content_type": "markdown",
      "tags": ["company", "context"],
      "created_at": "2025-01-10T00:00:00Z"
    }
  ]
}
```

### POST `/memory/global`

Create a global memory entry.

**Request:**
```json
{
  "key": "q3_targets",
  "content": "Q3 revenue target: $5M. Cost reduction goal: 15%.",
  "content_type": "text",
  "tags": ["finance", "targets", "q3"]
}
```

**Response 201:** Full GlobalMemory object.

### PUT `/memory/global/{id}`

Update a memory entry.

### DELETE `/memory/global/{id}`

Remove a memory entry.

---

## 10. System

### GET `/system/health`

Health check — no auth required.

**Response 200:**
```json
{
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "worker": "running"
    },
    "timestamp": "2025-01-15T10:00:00Z"
  }
}
```

**Response 503** (any service down):
```json
{
  "data": {
    "status": "degraded",
    "services": {
      "database": "healthy",
      "redis": "unhealthy",
      "worker": "unknown"
    }
  }
}
```

### GET `/system/stats`

Aggregate statistics for the dashboard.

**Response 200:**
```json
{
  "data": {
    "agents": {
      "total": 8,
      "by_status": { "IDLE": 5, "WORKING": 2, "ERROR": 1, "OFFLINE": 0 }
    },
    "tasks": {
      "total": 147,
      "by_status": {
        "BACKLOG": 12,
        "IN_PROGRESS": 3,
        "IN_REVIEW": 2,
        "DONE": 128,
        "FAILED": 2
      }
    },
    "costs": {
      "today_usd": 0.83,
      "this_month_usd": 14.22,
      "by_provider": {
        "OPENAI": 9.10,
        "ANTHROPIC": 5.12
      }
    },
    "llm_calls": {
      "today": 142,
      "this_month": 2841
    }
  }
}
```

---

## 11. Messaging Channels

Manage connections to external messaging platforms (Telegram, WhatsApp, Discord, Slack).

### GET `/messaging/channels`

List all configured messaging channels.

**Response `200`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "platform": "telegram",
      "name": "Main Telegram Bot",
      "is_active": true,
      "assigned_agent_id": null,
      "webhook_url": "https://yourdomain.com/api/v1/webhooks/telegram/{id}",
      "created_at": "2024-01-15T12:00:00Z"
    }
  ]
}
```

### POST `/messaging/channels`

Create a new messaging channel.

**Request:**
```json
{
  "platform": "telegram",
  "name": "Main Telegram Bot",
  "is_active": true,
  "config": {
    "bot_token_ref": "TELEGRAM_BOT_TOKEN",
    "secret_token_ref": "TELEGRAM_SECRET_TOKEN"
  },
  "assigned_agent_id": null
}
```

**Response `201`:** Full channel object including `webhook_url`.

### PUT `/messaging/channels/{id}`

Update channel config (rename, enable/disable, change credentials refs, reassign agent).

### DELETE `/messaging/channels/{id}`

Remove a channel. Existing Conversation records are retained.

### GET `/messaging/channels/{id}/conversations`

List conversations on a channel with last message preview and unread count.

**Response `200`:**
```json
{
  "data": [
    {
      "id": "uuid",
      "channel_id": "uuid",
      "external_user_id": "123456789",
      "external_chat_id": "123456789",
      "last_message": "Can you check the sales report?",
      "last_message_at": "2024-01-15T12:05:00Z",
      "message_count": 14
    }
  ]
}
```

---

## 12. Webhooks (Inbound Messaging)

These endpoints receive events from external platforms. They are **not authenticated with JWT** — each uses the platform's own signature verification mechanism.

### POST `/webhooks/telegram/{channel_id}`

Receives Telegram Update objects. Verifies `X-Telegram-Bot-Api-Secret-Token` header.

### GET `/webhooks/whatsapp/{channel_id}`

WhatsApp verification challenge. Responds with `hub.challenge` if `hub.verify_token` matches.

### POST `/webhooks/whatsapp/{channel_id}`

Receives WhatsApp messages. Verifies `X-Hub-Signature-256` HMAC header.

### POST `/webhooks/discord/{channel_id}`

Receives Discord Interactions. Verifies Ed25519 signature. Returns `{"type": 1}` for PING.

### POST `/webhooks/slack/{channel_id}`

Receives Slack Events API payloads. Verifies `X-Slack-Signature` HMAC. Returns `{"challenge": "..."}` for URL verification.

**All webhook endpoints return `200 {"ok": true}` on success.** Errors return `401` (bad signature) or `404` (unknown channel). Processing is async — a fast `200` is always returned before orchestrator processing completes.

---

## 13. WebSocket API

### Connection

```
ws://{host}/ws?token={jwt_token}
```

Auth token passed as query parameter on WS connection.

### Client → Server Messages

After connecting, clients send JSON messages to subscribe to specific channels:

```json
// Subscribe to global activity feed
{ "action": "subscribe", "channel": "global" }

// Subscribe to specific agent updates
{ "action": "subscribe", "channel": "agent", "agent_id": "uuid" }

// Subscribe to specific task updates
{ "action": "subscribe", "channel": "task", "task_id": "uuid" }

// Subscribe to Kanban board updates
{ "action": "subscribe", "channel": "kanban" }

// Unsubscribe
{ "action": "unsubscribe", "channel": "global" }
```

### Server → Client Events

All events follow this envelope:

```json
{
  "type": "<event_type>",
  "channel": "<channel_name>",
  "payload": { ...event data... },
  "timestamp": "2025-01-15T10:00:00Z"
}
```

#### `agent_status_changed`
Triggered when an agent's status changes.
```json
{
  "type": "agent_status_changed",
  "channel": "agent",
  "payload": {
    "agent_id": "...",
    "agent_name": "Sofia",
    "old_status": "IDLE",
    "new_status": "WORKING",
    "current_task_id": "...",
    "current_task_title": "Q3 Analysis"
  }
}
```

#### `task_status_changed`
Triggered when a task moves between Kanban columns.
```json
{
  "type": "task_status_changed",
  "channel": "kanban",
  "payload": {
    "task_id": "...",
    "task_title": "Q3 Analysis",
    "old_status": "IN_PROGRESS",
    "new_status": "DONE",
    "assigned_agent_id": "...",
    "assigned_agent_name": "Sofia"
  }
}
```

#### `task_event_created`
Triggered when a new TaskEvent is appended to a task.
```json
{
  "type": "task_event_created",
  "channel": "task",
  "payload": {
    "task_id": "...",
    "event_id": "...",
    "event_type": "TOOL_CALL",
    "agent_id": "...",
    "agent_name": "Sofia",
    "payload": {
      "tool_name": "finance_api",
      "input": { "method": "GET", "path": "/q3/summary" },
      "success": true,
      "duration_ms": 342
    }
  }
}
```

#### `activity_feed`
Global activity stream — human-readable log entries.
```json
{
  "type": "activity_feed",
  "channel": "global",
  "payload": {
    "message": "Sofia called tool: Finance API (GET /q3/summary) → 200 OK",
    "agent_id": "...",
    "agent_name": "Sofia",
    "agent_domain": "FINANCE",
    "task_id": "...",
    "task_title": "Q3 Analysis",
    "severity": "info"
  }
}
```

Severity values: `info`, `warning`, `error`, `success`

#### `agent_heartbeat`
Sent every 30 seconds for each active agent.
```json
{
  "type": "agent_heartbeat",
  "channel": "agent",
  "payload": {
    "agent_id": "...",
    "status": "WORKING",
    "iteration": 3,
    "current_task_id": "..."
  }
}
```

#### `chat_response`
Orchestrator response during streaming (chunked).
```json
{
  "type": "chat_response",
  "channel": "global",
  "payload": {
    "chunk": "I'll analyze that for you...",
    "is_final": false
  }
}
```
Final chunk: `{ "chunk": "", "is_final": true, "actions_taken": [...] }`

---

## 12. FastAPI Router Implementation Pattern

```python
# backend/app/routers/agents.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from ..core.deps import get_session, get_current_user
from ..services.agent_service import AgentService
from ..schemas.agent import AgentCreate, AgentUpdate, AgentRead, AgentDetail
from ..schemas.common import PaginatedResponse, SuccessResponse
from ..models.enums import AgentStatusEnum, DomainEnum

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("", response_model=SuccessResponse[PaginatedResponse[AgentRead]])
async def list_agents(
    status: Optional[AgentStatusEnum] = Query(None),
    domain: Optional[DomainEnum] = Query(None),
    is_orchestrator: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _user = Depends(get_current_user),
):
    service = AgentService(session)
    agents, total = await service.list(
        status=status, domain=domain,
        is_orchestrator=is_orchestrator,
        page=page, limit=limit
    )
    return SuccessResponse(data=PaginatedResponse(
        items=agents, total=total, page=page,
        limit=limit, total_pages=(total + limit - 1) // limit
    ))

@router.post("", response_model=SuccessResponse[AgentDetail], status_code=201)
async def create_agent(
    body: AgentCreate,
    session: AsyncSession = Depends(get_session),
    _user = Depends(get_current_user),
):
    service = AgentService(session)
    agent = await service.create(body)
    return SuccessResponse(data=agent)

# ... etc for GET /{id}, PUT /{id}, DELETE /{id}, PATCH /{id}/status
```

---

## 13. Pydantic Schema Patterns

```python
# backend/app/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    data: T

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str

class ErrorResponse(BaseModel):
    error: dict  # {code, message, details}
```

```python
# backend/app/schemas/agent.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from ..models.enums import GenderEnum, DomainEnum, AgentStatusEnum

class PersonalityConfig(BaseModel):
    detail_oriented: int = Field(50, ge=0, le=100)
    risk_tolerance: int = Field(50, ge=0, le=100)
    formality: int = Field(50, ge=0, le=100)
    strengths: List[str] = []
    weaknesses: List[str] = []
    communication_style: str = ""

class AvatarConfig(BaseModel):
    sprite_id: str
    color_primary: str
    color_secondary: str
    icon: str
    desk_position: dict = Field(default_factory=lambda: {"x": 0, "y": 0})

class ToolAssignment(BaseModel):
    tool_id: UUID
    permissions: str  # READ_ONLY | READ_WRITE | DANGEROUS

class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    gender: GenderEnum
    class_id: UUID
    domain: DomainEnum
    role_description: str = Field(max_length=500)
    personality: PersonalityConfig = Field(default_factory=PersonalityConfig)
    llm_config_id: UUID
    avatar_config: AvatarConfig
    is_orchestrator: bool = False
    tool_assignments: List[ToolAssignment] = []

class AgentRead(BaseModel):
    id: UUID
    name: str
    gender: GenderEnum
    class_id: UUID
    class_name: str
    domain: DomainEnum
    status: AgentStatusEnum
    is_orchestrator: bool
    current_task_id: Optional[UUID]
    current_task_title: Optional[str]
    avatar_config: dict
    created_at: datetime
    updated_at: datetime
```
