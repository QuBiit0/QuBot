# Qubot — System Architecture

> **Version**: 1.0 | **Stack**: FastAPI + PostgreSQL + Redis + Next.js

---

## 1. System Overview

Qubot is a self-hosted, visual multi-agent AI platform that runs as a Mission Control for teams of AI agents. Users interact with a single **orchestrator agent** through a chat interface or directly from **external messaging apps**; the orchestrator delegates work to specialized **sub-agents**, each with their own roles, personalities, LLM configurations, and tool access.

The system is distinguishable by:
- **Gamified coworking office UI** — agents appear as video game characters at desks, with visual states (working, idle, error, offline)
- **100% visual configuration** — create agents, assign LLMs, configure tools, all without code
- **Multi-provider LLM support** — configurable per agent (OpenAI, Anthropic, Google, Groq, Ollama)
- **Event-driven real-time updates** — WebSocket + Redis pub/sub for live Kanban, activity feed, agent status
- **Messaging platform integrations** — interact with your agent team via Telegram, WhatsApp, Discord, and Slack

**Design Principles:**
1. **Stateless agents** — no in-memory state; all persistence goes to PostgreSQL/Redis
2. **Tool-first reasoning** — the LLM decides, tools execute; agents never run code directly
3. **Observable execution** — every LLM call, tool invocation, and task state change is logged
4. **Event-driven UI** — frontend reacts to server events, never polls
5. **Separation of layers** — Routers → Services → Repositories; no business logic in HTTP handlers

---

## 2. C4 Level 1 — System Context

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL WORLD                             │
│                                                                         │
│  ┌──────────┐    HTTP/WS     ┌──────────────────────────────────────┐  │
│  │          │ ──────────────▶│                                      │  │
│  │   User   │                │          Qubot Platform              │  │
│  │(Browser) │ ◀────────────── │    (Web App + Backend + Workers)    │  │
│  └──────────┘    HTTP/WS     │                                      │  │
│                              └──────────┬───────────────────────────┘  │
│                                         │                               │
│              ┌──────────────────────────┼──────────────────────────┐   │
│              │                          │                           │   │
│              ▼                          ▼                           ▼   │
│   ┌──────────────────┐   ┌──────────────────────┐   ┌───────────────┐ │
│   │  LLM Providers   │   │   External APIs /    │   │  File System  │ │
│   │                  │   │   Web / Shell        │   │  (sandboxed)  │ │
│   │ • OpenAI         │   │                      │   └───────────────┘ │
│   │ • Anthropic      │   │  (tool execution     │                      │
│   │ • Google         │   │   targets)           │                      │
│   │ • Groq           │   └──────────────────────┘                      │
│   │ • Ollama (local) │                                                  │
│   └──────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. C4 Level 2 — Container Diagram

Five containers form the Qubot platform:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          QUBOT PLATFORM                                  │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Telegram │  │WhatsApp  │  │ Discord  │  │  Slack   │  (external)   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       └─────────────┴─────────────┴──────────────┘                     │
│                            │ webhook POST                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  qubot-frontend  (Next.js 14, port 3000)                        │    │
│  │                                                                 │    │
│  │  • Coworking canvas (Konva.js)        • Agent creation wizard   │    │
│  │  • Kanban board (dnd-kit)             • Tool editor             │    │
│  │  • Activity feed (live WebSocket)     • LLM config manager      │    │
│  │  • Orchestrator chat UI               • Messaging channel mgmt  │    │
│  └──────────────────────────────┬────────────────────────────────┘     │
│                                  │ HTTP REST + WebSocket                 │
│  ┌───────────────────────────────▼────────────────────────────────┐    │
│  │  qubot-api  (FastAPI Python 3.12, port 8000)                   │    │
│  │                                                                 │    │
│  │  • REST API (all CRUD)                                          │    │
│  │  • WebSocket hub (real-time events)                             │    │
│  │  • Orchestrator endpoint (/chat)                                │    │
│  │  • Messaging ingress (webhooks: Telegram/WhatsApp/Discord/Slack)│    │
│  │  • Action handler (CREATE_TASK, ASSIGN_TASK, etc.)              │    │
│  └──────┬─────────────────────────────┬──────────────────────────┘     │
│         │ SQL (asyncpg)                │ Redis pub/sub + streams         │
│         │                             │                                  │
│  ┌──────▼──────────┐       ┌──────────▼─────────────────────────┐      │
│  │   qubot-db      │       │  qubot-redis  (Redis 7, port 6379) │      │
│  │  (PostgreSQL 16 │       │                                     │      │
│  │   port 5432)    │       │  • Task queues (Redis Streams)      │      │
│  │                 │       │  • WS event bus (pub/sub)           │      │
│  │  All persistent │       │  • Session cache                    │      │
│  │  state          │       │  • Rate limiting counters           │      │
│  └─────────────────┘       └──────────┬──────────────────────────┘     │
│                                        │ Redis Streams (XREAD)           │
│  ┌─────────────────────────────────────▼──────────────────────────┐    │
│  │  qubot-worker  (Python asyncio process)                         │    │
│  │                                                                 │    │
│  │  • Consumes task queue from Redis Streams                       │    │
│  │  • Runs agent execution loop (LLM → tool calls → repeat)       │    │
│  │  • Executes tools (HTTP, shell, browser, filesystem)            │    │
│  │  • Writes TaskEvents to PostgreSQL                              │    │
│  │  • Broadcasts activity events via Redis pub/sub → WebSocket    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

### Container Responsibilities

| Container | Technology | Port | Responsibility |
|-----------|-----------|------|---------------|
| `qubot-frontend` | Next.js 14 + React 18 + TypeScript | 3000 | All UI — coworking canvas, Kanban, wizards, chat |
| `qubot-api` | FastAPI Python 3.12 | 8000 | REST API, WebSocket hub, orchestrator, action dispatch |
| `qubot-worker` | Python asyncio | — | Task execution loop, tool runner, LLM agentic loops |
| `qubot-db` | PostgreSQL 16 | 5432 | All persistent data (agents, tasks, events, memory) |
| `qubot-redis` | Redis 7 | 6379 | Task queues, WebSocket event bus, cache |

---

## 4. C4 Level 3 — Components (inside qubot-api)

```
┌───────────────────────────────────────────────────────────────────┐
│                         qubot-api                                 │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Routers    │  │   Services   │  │     Tool Impls       │   │
│  │ (HTTP layer) │  │(Biz logic)   │  │                      │   │
│  │              │  │              │  │  • HttpApiTool        │   │
│  │  /agents     │  │  agent_svc   │  │  • SystemShellTool   │   │
│  │  /tasks      │  │  task_svc    │  │  • WebBrowserTool    │   │
│  │  /tools      │  │  tool_svc    │  │  • FilesystemTool    │   │
│  │  /llm-cfg    │  │  llm_svc     │  │  • SchedulerTool     │   │
│  │  /chat       │  │  orch_svc    │  │  • CustomTool        │   │
│  │  /memory     │  │  assign_svc  │  └──────────────────────┘   │
│  │  /system     │  │  memory_svc  │                              │
│  │  /ws         │  └──────┬───────┘  ┌──────────────────────┐   │
│  └──────┬───────┘         │          │    LLM Providers     │   │
│         │                 │          │                      │   │
│         │         ┌───────▼───────┐  │  • OpenAiProvider    │   │
│         │         │    Models     │  │  • AnthropicProvider │   │
│         │         │  (SQLModel)   │  │  • GoogleProvider    │   │
│         │         │               │  │  • GroqProvider      │   │
│         │         │  Agent        │  │  • OllamaProvider    │   │
│         │         │  AgentClass   │  └──────────────────────┘   │
│         │         │  Task         │                              │
│         │         │  TaskEvent    │  ┌──────────────────────┐   │
│         │         │  Tool         │  │  Realtime Module     │   │
│         │         │  LlmConfig    │  │                      │   │
│         │         │  Memory*      │  │  ConnectionManager   │   │
│         │         └───────────────┘  │  (WS + Redis sub)   │   │
│         │                            │  broadcast_* helpers │   │
│         └───────────────────────────▶└──────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### Module Descriptions

| Module | Path | Responsibility |
|--------|------|---------------|
| `agents` | `routers/agents.py` + `services/agent_service.py` | CRUD agents, status management, tool assignment |
| `agent_classes` | `routers/agent_classes.py` + `services/agent_class_service.py` | Predefined + custom class management |
| `tasks` | `routers/tasks.py` + `services/task_service.py` | Task lifecycle, Kanban state machine, event log |
| `tools` | `routers/tools.py` + `services/tool_service.py` + `tools_impl/` | Tool registry, config, execution dispatch |
| `llm` | `routers/llm_configs.py` + `services/llm_service.py` + `llm/` | Provider abstraction, cost tracking, connectivity test |
| `orchestrator` | `routers/chat.py` + `services/orchestrator_service.py` | Chat endpoint, action parsing, task dispatch |
| `assignment` | `services/assignment_service.py` | Agent selection algorithm |
| `execution` | `services/execution_service.py` (used by worker) | Agent execution loop, tool calling |
| `memory` | `routers/memory.py` + `services/memory_service.py` | Global/agent/task memory CRUD + context injection |
| `realtime` | `realtime/manager.py` + `realtime/events.py` | WebSocket connection manager, Redis pub/sub bridge |
| `core` | `core/` | JWT auth, logging, exception handlers, DI deps |
| `seeds` | `seeds/` | Initial data (17 predefined AgentClass records) |

---

## 5. Data Flow Diagrams

### 5.1 User Chat → Task Execution (Happy Path)

```
User                   Frontend            qubot-api          qubot-worker        LLM Provider
 │                        │                    │                    │                   │
 │  "Analyze our Q3       │                    │                    │                   │
 │   financial data"      │                    │                    │                   │
 │───────────────────────▶│                    │                    │                   │
 │                        │  POST /chat        │                    │                   │
 │                        │───────────────────▶│                    │                   │
 │                        │                    │  Build orchestrator│                   │
 │                        │                    │  system prompt     │                   │
 │                        │                    │  (team context,    │                   │
 │                        │                    │   recent tasks)    │                   │
 │                        │                    │──────────────────────────────────────▶│
 │                        │                    │                    │  {response,       │
 │                        │                    │◀──────────────────────────────────────│
 │                        │                    │                    │   actions:[       │
 │                        │                    │  Parse actions     │    CREATE_TASK,   │
 │                        │                    │  Execute actions:  │    ASSIGN_TASK]}  │
 │                        │                    │  • Insert Task     │                   │
 │                        │                    │  • Assign to       │                   │
 │                        │                    │    Finance agent   │                   │
 │                        │                    │  • Push to Redis   │                   │
 │                        │                    │    Stream          │                   │
 │                        │  WS: task_created  │                    │                   │
 │                        │◀───────────────────│                    │                   │
 │  "Got it! Creating     │                    │                    │                   │
 │   task for Finance     │                    │  XREAD from        │                   │
 │   Manager..."          │                    │  Redis Stream     ─┤                   │
 │◀───────────────────────│                    │                    │                   │
 │                        │                    │                    │  Build agent      │
 │                        │                    │                    │  prompt (task +   │
 │                        │                    │                    │  tools + memory)  │
 │                        │                    │                    │──────────────────▶│
 │                        │                    │                    │                   │
 │                        │  WS: agent         │                    │  {tool_calls:     │
 │                        │  status=WORKING    │                    │◀──────────────────│
 │                        │◀───────────────────│  WS broadcasts     │  [http_api(GET   │
 │                        │                    │  from worker via   │   /financials)]}  │
 │                        │  WS: activity_feed │  Redis pub/sub     │                   │
 │                        │◀───────────────────│                    │  Execute tool     │
 │                        │                    │                    │  → HTTP call      │
 │                        │  WS: task_event    │                    │  → Store event    │
 │                        │  (TOOL_CALL)       │                    │  → Feed result    │
 │                        │◀───────────────────│                    │    back to LLM    │
 │                        │                    │                    │──────────────────▶│
 │                        │                    │                    │  {finish: stop,   │
 │                        │                    │                    │◀──────────────────│
 │                        │                    │                    │  "COMPLETED:..."}  │
 │                        │                    │                    │  Update task=DONE │
 │                        │                    │                    │  Update agent=IDLE│
 │                        │  WS: task_done     │                    │                   │
 │                        │◀───────────────────│                    │                   │
 │  Kanban card moves     │                    │                    │                   │
 │  to "Done" column      │                    │                    │                   │
```

### 5.2 WebSocket Event Broadcasting

```
qubot-worker
     │
     │  await redis.publish("ws:kanban", event_json)
     │  await redis.publish("ws:global", activity_json)
     │  await redis.publish("ws:agent:{id}", status_json)
     │
     ▼
Redis Pub/Sub
     │
     │  (all qubot-api instances subscribed to "ws:*")
     │
     ▼
qubot-api ConnectionManager
     │  (listen_redis background task)
     │
     ├──▶ ws:kanban subscribers → broadcast to all WS clients
     ├──▶ ws:global subscribers → broadcast to all WS clients
     └──▶ ws:agent:{id} subscribers → broadcast to subscribed WS clients
```

---

## 6. Architecture Decision Records (ADRs)

### ADR-001: FastAPI over Flask or Django
**Decision**: Use FastAPI with async SQLAlchemy.
**Rationale**: FastAPI provides native async support (critical for concurrent LLM calls + WebSockets), automatic OpenAPI docs, and type-safe Pydantic schemas. Django is too heavy; Flask lacks native async.

### ADR-002: SQLModel for ORM
**Decision**: Use SQLModel (SQLAlchemy + Pydantic unified).
**Rationale**: Eliminates duplicate schema definitions. One class serves as both the DB model and the API schema base. Reduces maintenance.

### ADR-003: Redis Streams for task queues
**Decision**: Redis Streams (XADD/XREAD) instead of Celery/RQ.
**Rationale**: Already using Redis for pub/sub. Streams provide persistent, consumer-group-aware queues without additional infrastructure. Simple enough for this workload.

### ADR-004: Separate worker process
**Decision**: qubot-worker is a separate process, not background tasks inside qubot-api.
**Rationale**: Task execution can be long-running (minutes). Separating the worker prevents blocking API request handlers and allows independent scaling.

### ADR-005: Redis pub/sub for WebSocket broadcasting
**Decision**: All WS broadcasts go through Redis pub/sub.
**Rationale**: Enables horizontal scaling (multiple qubot-api instances) without sticky sessions. All instances receive all events and forward to their own WS clients.

### ADR-006: LLM provider abstraction layer
**Decision**: Never call LLM SDKs directly from services; always use the provider abstraction.
**Rationale**: Agents can be reconfigured to use any provider without code changes. Makes testing easy (mock the provider). Centralizes cost tracking and retry logic.

### ADR-007: API key references, not values
**Decision**: LlmConfig stores the ENV VAR NAME (e.g., `"OPENAI_API_KEY"`), not the actual key.
**Rationale**: Keys never touch the database. Operators manage secrets via environment variables or a vault. Prevents accidental key exposure in DB dumps or logs.

---

## 7. Security Architecture

### Authentication
- JWT tokens (HS256, configurable to RS256)
- Tokens expire in 60 minutes (configurable)
- All API routes require `Authorization: Bearer <token>` except `/system/health`

### Tool Execution Security
- `SystemShellTool`: command whitelist enforced before execution
- `FilesystemTool`: path traversal protection, jailed to `base_directory`
- `HttpApiTool`: domain whitelist in tool config; no localhost calls by default
- All tool calls: `asyncio.wait_for(..., timeout=60.0)` hard limit
- Tools with `is_dangerous=True` require `PermissionEnum.DANGEROUS` assignment

### Data Security
- API keys stored as env var references, never values
- Passwords hashed with bcrypt
- No PII logged (structlog sanitization)
- CORS restricted to `CORS_ORIGINS` config list

---

## 8. Scalability Considerations

| Concern | Solution |
|---------|---------|
| Multiple API instances | Redis pub/sub for WS broadcasting (all instances receive all events) |
| Heavy task workloads | Scale worker replicas independently |
| LLM rate limits | Tenacity retry with backoff per provider; cost limits per agent config |
| DB connection pooling | asyncpg connection pool (size configurable) |
| Large WebSocket fan-out | Channel-based subscriptions; clients only receive relevant events |

---

## 9. Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend API | FastAPI | 0.115+ |
| Python | Python | 3.12+ |
| ORM | SQLModel + SQLAlchemy | 0.0.21+ / 2.0+ |
| Validation | Pydantic | v2 |
| Database | PostgreSQL | 16 |
| Cache / Queues | Redis | 7 |
| Migrations | Alembic | 1.13+ |
| Logging | structlog | 24+ |
| HTTP client | httpx | 0.27+ |
| HTML parsing | BeautifulSoup4 | 4.12+ |
| Retry logic | tenacity | 8+ |
| Frontend | Next.js | 14 (App Router) |
| UI components | Shadcn/ui + TailwindCSS | latest |
| Canvas | Konva.js | 9+ |
| State management | Zustand + TanStack Query | latest |
| Animations | Framer Motion | 11+ |
| Drag & drop | dnd-kit | 6+ |
| Auth | JWT (python-jose) | 3.3+ |
| Container | Docker + docker-compose | latest |
| Reverse proxy | Nginx | 1.25+ |
