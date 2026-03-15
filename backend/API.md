# Qubot API Documentation

## Overview

Qubot is a multi-agent AI platform that provides a REST API and WebSocket support for real-time communication.

**Base URL:** `http://localhost:8000/api/v1`

**WebSocket URL:** `ws://localhost:8000/ws`

## Authentication

Currently, the API is open for development. In production, authentication will be required via JWT tokens.

## Endpoints

### System

#### Health Check
```http
GET /api/v1/health
```

Returns the health status of all services (API, Database, Redis).

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-13T10:30:00",
  "uptime_seconds": 3600,
  "checks": {
    "api": {"status": "healthy"},
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  }
}
```

#### System Info
```http
GET /api/v1/info
```

Returns system information and version.

#### Metrics
```http
GET /api/v1/metrics
```

Returns current system metrics (tasks, agents, recent events).

### Agents

#### List Agents
```http
GET /api/v1/agents
```

Query params:
- `status`: Filter by status (idle, working, error, offline)
- `domain`: Filter by domain
- `skip`: Pagination offset
- `limit`: Page size

#### Create Agent
```http
POST /api/v1/agents
```

**Body:**
```json
{
  "name": "My Agent",
  "gender": "neutral",
  "class_id": "uuid",
  "domain": "software",
  "llm_config_id": "uuid",
  "personality": {"analytical": 0.8, "creative": 0.6},
  "avatar_config": {"color": "#3B82F6"}
}
```

#### Get Agent
```http
GET /api/v1/agents/{agent_id}
```

#### Update Agent Status
```http
PATCH /api/v1/agents/{agent_id}/status
```

**Body:**
```json
{
  "status": "working",
  "current_task_id": "uuid"
}
```

### Agent Classes

#### List Agent Classes
```http
GET /api/v1/agent-classes
```

Returns all predefined agent classes (Developer, Data Scientist, Finance Manager, etc.).

### Tasks

#### List Tasks
```http
GET /api/v1/tasks
```

Query params:
- `status`: Filter by status (backlog, in_progress, done, failed)
- `domain`: Filter by domain
- `assigned_agent_id`: Filter by agent
- `skip`: Pagination offset
- `limit`: Page size

#### Create Task
```http
POST /api/v1/tasks
```

**Body:**
```json
{
  "title": "Build API",
  "description": "Create REST API with FastAPI",
  "priority": "high",
  "domain_hint": "software",
  "input_data": {"requirements": [...]}
}
```

#### Update Task Status
```http
PATCH /api/v1/tasks/{task_id}/status
```

**Body:**
```json
{
  "status": "in_progress"
}
```

#### Assign Task
```http
PATCH /api/v1/tasks/{task_id}/assign
```

**Body:**
```json
{
  "agent_id": "uuid"
}
```

#### Execute Task (Synchronous)
```http
POST /api/v1/tasks/{task_id}/execute
```

Executes the task immediately with the assigned agent.

**Body:**
```json
{
  "max_iterations": 10
}
```

#### Submit Task (Asynchronous)
```http
POST /api/v1/tasks/{task_id}/submit
```

Submits the task to the worker queue for background processing.

#### Get Assignment Recommendations
```http
GET /api/v1/tasks/{task_id}/assignments?top_k=3
```

Returns top-k agent recommendations for the task with scoring breakdown.

#### Auto-Assign Task
```http
POST /api/v1/tasks/{task_id}/auto-assign
```

Automatically assigns the task to the best available agent.

**Body:**
```json
{
  "force": false
}
```

#### Get Kanban Board
```http
GET /api/v1/tasks/kanban/board
```

Returns all tasks organized by status for Kanban view.

### Orchestrator

#### Process Task
```http
POST /api/v1/orchestrator/process
```

Submits a high-level task to the orchestrator for automatic decomposition and execution.

**Body:**
```json
{
  "title": "Create a Python API",
  "description": "Build a REST API with FastAPI that...",
  "llm_config_id": "uuid",
  "priority": "high",
  "domain": "software"
}
```

### LLM Configs

#### List LLM Configs
```http
GET /api/v1/llm-configs
```

#### Create LLM Config
```http
POST /api/v1/llm-configs
```

**Body:**
```json
{
  "name": "GPT-4o",
  "provider": "openai",
  "model_name": "gpt-4o",
  "api_key_ref": "OPENAI_API_KEY",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

#### Test Connection
```http
POST /api/v1/llm-configs/{config_id}/test
```

Tests connectivity to the LLM provider.

#### Chat Completion
```http
POST /api/v1/llm-configs/{config_id}/chat
```

**Body:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "system_prompt": "You are a helpful assistant.",
  "tools": [...]
}
```

### Tools

#### List Available Tools
```http
GET /api/v1/tools/available
```

Returns all available tools with their JSON schemas.

#### Execute Tool
```http
POST /api/v1/tools/execute
```

**Body:**
```json
{
  "tool_name": "http_api",
  "params": {
    "url": "https://api.example.com/data",
    "method": "GET"
  },
  "task_id": "uuid"
}
```

#### Execute with LLM
```http
POST /api/v1/tools/execute-with-llm
```

Executes an LLM completion with automatic tool calling.

**Body:**
```json
{
  "llm_config_id": "uuid",
  "messages": [{"role": "user", "content": "Search for..."}],
  "max_iterations": 5
}
```

### Memories

#### List Global Memories
```http
GET /api/v1/memories/global
```

#### Create Global Memory
```http
POST /api/v1/memories/global
```

**Body:**
```json
{
  "key": "api_endpoints",
  "content": "List of API endpoints...",
  "tags": ["api", "documentation"]
}
```

#### Get Agent Memories
```http
GET /api/v1/agents/{agent_id}/memories
```

## WebSocket

### Connection

Connect to: `ws://localhost:8000/ws`

### Client → Server Messages

#### Subscribe to Events
```json
{
  "action": "subscribe",
  "events": ["task.completed", "agent.status_changed"]
}
```

#### Ping
```json
{
  "action": "ping"
}
```

### Server → Client Messages

#### Task Events
```json
{
  "type": "task.completed",
  "payload": {
    "task_id": "uuid",
    "status": "completed",
    "agent_id": "uuid"
  },
  "timestamp": "2024-03-13T10:30:00"
}
```

#### Agent Status
```json
{
  "type": "agent.status_changed",
  "payload": {
    "agent_id": "uuid",
    "status": "working",
    "current_task_id": "uuid"
  },
  "timestamp": "2024-03-13T10:30:00"
}
```

#### Activity Log
```json
{
  "type": "activity.log",
  "payload": {
    "type": "tool_execution",
    "description": "Executed http_api tool",
    "agent_id": "uuid",
    "task_id": "uuid"
  },
  "timestamp": "2024-03-13T10:30:00"
}
```

#### Metrics Update
```json
{
  "type": "metrics.updated",
  "payload": {
    "tasks": {"total": 10, "completed": 5, "active": 3},
    "agents": {"total": 5, "active": 2}
  }
}
```

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable (health check)

## Rate Limiting

Rate limiting is not currently implemented but should be added for production use.

## Examples

### Create and Execute a Task

```bash
# 1. Create a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Analyze data",
    "description": "Analyze the sales data and create a report",
    "domain_hint": "data"
  }'

# 2. Get assignment recommendations
curl http://localhost:8000/api/v1/tasks/{task_id}/assignments

# 3. Auto-assign task
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/auto-assign

# 4. Execute task
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/execute \
  -H "Content-Type: application/json" \
  -d '{"max_iterations": 10}'
```

### WebSocket Connection (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected');
  
  // Subscribe to events
  ws.send(JSON.stringify({
    action: 'subscribe',
    events: ['task.completed', 'agent.status_changed']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```
