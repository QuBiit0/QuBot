# Qubot Backend Architecture

## Overview

Qubot is a multi-agent AI platform built with Python, FastAPI, and PostgreSQL. It provides a scalable backend for orchestrating AI agents, managing tasks, and executing tools.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Frontend │  │   CLI    │  │  Mobile  │  │  API     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                    ┌────────▼────────┐
                    │   Load Balancer │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│   API Instance │  │   API Instance │  │   API Instance │
│      (Pod 1)   │  │      (Pod 2)   │  │      (Pod N)   │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
│   PostgreSQL   │  │     Redis      │  │    Workers     │
│   (Database)   │  │  (Cache/Queue) │  │  (Task Proc)   │
└────────────────┘  └────────────────┘  └────────────────┘
```

## Core Components

### 1. API Layer (FastAPI)

**Routers:**
- `agents.py` - Agent management
- `tasks.py` - Task CRUD and Kanban
- `tools.py` - Tool registry
- `llm_configs.py` - LLM configuration
- `memories.py` - Memory management
- `tool_execution.py` - Tool execution
- `execution.py` - Task execution & orchestration
- `system.py` - Health checks & metrics
- `websocket.py` - Real-time communication

### 2. Service Layer

**Core Services:**
- `AgentService` - Agent CRUD, assignments
- `TaskService` - Task lifecycle management
- `ToolService` - Tool registry management
- `LLMService` - LLM configuration & cost tracking
- `MemoryService` - Memory storage & retrieval

**Execution Services:**
- `ExecutionService` - Agent execution loop
- `OrchestratorService` - Multi-agent coordination
- `AssignmentService` - Intelligent task assignment
- `ToolExecutionService` - Tool execution with LLM

### 3. Provider Layer

**LLM Providers:**
- `OpenAiProvider` - GPT-4, GPT-3.5
- `AnthropicProvider` - Claude 3.x
- `GoogleProvider` - Gemini
- `GroqProvider` - Llama, Mixtral
- `OllamaProvider` - Local models

**Tools:**
- `HttpApiTool` - HTTP requests
- `SystemShellTool` - Shell commands
- `WebBrowserTool` - Web scraping
- `FilesystemTool` - File operations
- `SchedulerTool` - Task scheduling

### 4. Infrastructure Layer

**Database:**
- SQLModel with async PostgreSQL
- 14 models with relationships
- Alembic migrations

**Cache/Queue:**
- Redis for caching
- Redis Streams for task queue
- Pub/Sub for real-time events

**Real-time:**
- WebSocket connections
- Connection manager with Redis
- Event broadcasting

## Data Flow

### Task Execution Flow

```
1. User creates task
   ↓
2. Orchestrator analyzes complexity
   ↓
3. AssignmentService scores agents
   ↓
4. Task assigned to best agent
   ↓
5. ExecutionService runs agent loop
   ├─ Load agent config
   ├─ Inject memory context
   ├─ Build system prompt
   ├─ Loop: LLM → Tools → Result
   └─ Save output to memory
   ↓
6. Task marked complete/failed
   ↓
7. Real-time notification sent
```

### Multi-Agent Orchestration

```
1. Complex task received
   ↓
2. Decomposed into subtasks
   ↓
3. Subtasks assigned to agents
   ↓
4. Parallel/sequential execution
   ↓
5. Results synthesized
   ↓
6. Final output delivered
```

## Key Features

### 1. Intelligent Assignment

Scoring algorithm considers:
- Domain expertise (0-40 points)
- Current workload (0-25 points)
- Past performance (0-25 points)
- Availability (0-10 points)

### 2. Memory System

Three-tier memory:
- **Global Memory** - Shared knowledge across agents
- **Agent Memory** - Agent-specific learnings
- **Task Memory** - Task execution history

### 3. Tool System

Risk-based access control:
- **Safe** - Read-only operations
- **Normal** - Standard operations
- **Dangerous** - Write/delete operations

### 4. Real-time Updates

WebSocket events:
- Task status changes
- Agent status updates
- Tool execution results
- Activity logs
- System notifications

## API Structure

### REST Endpoints

```
/api/v1/
├── system/
│   ├── health          # Health check
│   ├── health/ready    # K8s readiness
│   ├── health/live     # K8s liveness
│   ├── metrics         # System metrics
│   ├── info            # System info
│   └── config          # Public config
├── agents/
│   ├── GET /           # List agents
│   ├── POST /          # Create agent
│   ├── GET /{id}       # Get agent
│   ├── PUT /{id}       # Update agent
│   ├── DELETE /{id}    # Delete agent
│   └── PATCH /{id}/status
├── tasks/
│   ├── GET /           # List tasks
│   ├── POST /          # Create task
│   ├── GET /{id}       # Get task
│   ├── PATCH /{id}/status
│   ├── PATCH /{id}/assign
│   ├── POST /{id}/execute
│   ├── POST /{id}/submit
│   └── GET /kanban/board
├── tools/
│   ├── GET /available  # List tools
│   ├── POST /execute   # Execute tool
│   └── POST /execute-with-llm
├── orchestrator/
│   └── POST /process   # Process complex task
└── llm-configs/
    ├── GET /
    ├── POST /
    ├── GET /{id}
    └── POST /{id}/chat
```

### WebSocket Endpoints

```
/ws                    # General updates
/ws/agents/{id}        # Agent-specific
/ws/tasks/{id}         # Task-specific
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk_...
OLLAMA_HOST=http://localhost:11434
```

## Deployment

### Docker Compose (Development)

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://qubot:pass@db:5432/qubot
      - REDIS_URL=redis://redis:6379/0
  
  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=qubot
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=qubot
  
  redis:
    image: redis:7-alpine
  
  worker:
    build: .
    command: python -m app.worker
    environment:
      - DATABASE_URL=postgresql+asyncpg://qubot:pass@db:5432/qubot
      - REDIS_URL=redis://redis:6379/0
```

### Kubernetes (Production)

- Deployment with multiple replicas
- Service for load balancing
- Ingress for external access
- ConfigMap for configuration
- Secrets for sensitive data
- PersistentVolume for database

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Structure

```
tests/
├── __init__.py
├── test_api.py          # Integration tests
└── test_services.py     # Unit tests
```

## Performance Considerations

### Database
- Connection pooling (asyncpg)
- Indexed columns for filtering
- Async queries throughout

### Caching
- Redis for session storage
- Tool result caching
- Agent configuration caching

### Scaling
- Stateless API instances
- Worker queue for background tasks
- Redis pub/sub for cross-instance communication

## Security

### Implemented
- API keys stored as env var references
- Tool sandboxing (filesystem, shell)
- Domain restrictions (browser tool)
- Command whitelisting (shell tool)

### TODO
- JWT authentication
- Rate limiting
- Request validation
- Audit logging

## Monitoring

### Health Checks
- `/health` - Overall health
- `/health/ready` - Ready for traffic
- `/health/live` - Application running

### Metrics
- Task counts by status
- Agent utilization
- LLM cost tracking
- Tool execution stats

## Future Improvements

1. **Authentication** - JWT-based auth
2. **Rate Limiting** - Prevent API abuse
3. **Audit Logging** - Complete activity trail
4. **Metrics Dashboard** - Visual monitoring
5. **Plugin System** - Custom tool plugins
6. **Multi-tenancy** - Organization support
