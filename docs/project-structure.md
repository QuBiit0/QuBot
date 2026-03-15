# Qubot — Project Structure

> **Complete annotated directory tree** — every file and its purpose.
> Use this as the authoritative reference when building the project from scratch.

---

## Top-Level Layout

```
qubot/
├── backend/                   # FastAPI application (API + Worker)
├── frontend/                  # Next.js 14 application
├── nginx/                     # Reverse proxy configuration
├── docs/                      # All specification documents
├── docker-compose.yml         # Development environment
├── docker-compose.prod.yml    # Production overrides
├── .env.example               # Environment variable template
├── .gitignore
└── README.md
```

---

## Backend

```
backend/
├── Dockerfile                 # Multi-stage Python 3.12 image
├── requirements.txt           # All Python dependencies pinned
├── alembic.ini                # Alembic migration config (script_location=alembic)
├── pyproject.toml             # Tool config: ruff linting, mypy type checking
│
├── alembic/
│   ├── env.py                 # Async Alembic env — connects to DATABASE_URL
│   ├── script.py.mako         # Migration file template
│   └── versions/
│       └── 001_initial_schema.py  # Full initial migration: all 12 tables + indexes
│
├── tests/
│   ├── conftest.py            # Fixtures: async test client, test DB session, factories
│   ├── unit/
│   │   ├── test_assignment_service.py   # Agent scoring algorithm tests
│   │   ├── test_orchestrator_service.py # Action parsing, JSON extraction
│   │   ├── test_tool_executor.py        # Permission enforcement, timeout
│   │   └── test_memory_service.py       # Context building, retrieval
│   └── integration/
│       ├── test_agents_api.py           # CRUD + status endpoints
│       ├── test_tasks_api.py            # Task lifecycle + Kanban moves
│       ├── test_tools_api.py            # Tool registry + test execution
│       └── test_chat_api.py             # Orchestrator chat → actions
│
└── app/
    ├── __init__.py
    ├── main.py                # FastAPI app factory (see below)
    ├── config.py              # Pydantic Settings — all env vars
    ├── database.py            # Async SQLAlchemy engine + get_session()
    ├── redis_client.py        # Redis connection singleton
    ├── worker.py              # Worker process entry point (run standalone)
    │
    ├── models/                # SQLModel ORM models — define DB tables
    │   ├── __init__.py        # Re-exports all models for Alembic discovery
    │   ├── enums.py           # All enums: DomainEnum, AgentStatusEnum, etc.
    │   ├── agent.py           # AgentClass, Agent, AgentTool models
    │   ├── task.py            # Task, TaskEvent models
    │   ├── tool.py            # Tool model
    │   ├── llm.py             # LlmConfig, LlmCallLog models
    │   └── memory.py          # GlobalMemory, AgentMemory, TaskMemory models
    │
    ├── schemas/               # Pydantic request/response schemas (no table=True)
    │   ├── __init__.py
    │   ├── agent.py           # AgentRead, AgentCreate, AgentUpdate, AgentDetail
    │   ├── task.py            # TaskRead, TaskCreate, TaskUpdate, TaskDetail
    │   ├── tool.py            # ToolRead, ToolCreate, ToolUpdate
    │   ├── llm.py             # LlmConfigRead, LlmConfigCreate
    │   ├── memory.py          # GlobalMemoryRead, GlobalMemoryCreate, AgentMemoryRead
    │   ├── chat.py            # ChatRequest, ChatResponse, OrchestratorAction
    │   └── websocket.py       # WsEvent, WsAgentStatus, WsTaskStatus, WsActivityFeed
    │
    ├── routers/               # FastAPI route handlers — thin layer, delegates to services
    │   ├── __init__.py
    │   ├── auth.py            # POST /auth/login, POST /auth/refresh
    │   ├── agents.py          # /agents CRUD + status + memory
    │   ├── agent_classes.py   # /agent-classes CRUD
    │   ├── tasks.py           # /tasks CRUD + status + events
    │   ├── tools.py           # /tools CRUD + test execution
    │   ├── llm_configs.py     # /llm-configs CRUD + connectivity test
    │   ├── chat.py            # POST /chat, GET /chat/history
    │   ├── memory.py          # /memory/global CRUD
    │   ├── system.py          # GET /system/health, GET /system/stats
    │   └── websocket.py       # WebSocket endpoint ws://host/ws
    │
    ├── services/              # Business logic — all application rules live here
    │   ├── __init__.py
    │   ├── agent_service.py        # Agent CRUD, status updates
    │   ├── task_service.py         # Task CRUD, state machine, event logging
    │   ├── tool_service.py         # Tool CRUD, test execution dispatch
    │   ├── llm_service.py          # LLM provider dispatch, cost tracking, call logging
    │   ├── orchestrator_service.py # /chat handler: builds context, calls LLM, executes actions
    │   ├── assignment_service.py   # find_best_agent() scoring algorithm
    │   ├── execution_service.py    # Agent execution loop (tool-calling, iteration, completion)
    │   └── memory_service.py       # Memory CRUD, context building, task summarization
    │
    ├── tools_impl/            # Concrete tool implementations
    │   ├── __init__.py
    │   ├── base.py            # BaseTool ABC, ToolResult model
    │   ├── registry.py        # get_tool_impl(tool: Tool) → BaseTool factory
    │   ├── http_api.py        # HttpApiTool — external HTTP API calls
    │   ├── shell.py           # SystemShellTool — whitelisted shell commands
    │   ├── browser.py         # WebBrowserTool — httpx + BeautifulSoup4
    │   ├── filesystem.py      # FilesystemTool — sandboxed read/write
    │   ├── scheduler.py       # SchedulerTool — creates future Task records
    │   └── memory_write.py    # MemoryWriteTool — agents write to AgentMemory
    │
    ├── llm/                   # LLM provider abstraction layer
    │   ├── __init__.py
    │   ├── base.py            # BaseLlmProvider ABC, LlmMessage, LlmResponse, LlmUsage
    │   ├── registry.py        # get_provider(config: LlmConfig) → BaseLlmProvider
    │   ├── openai.py          # OpenAiProvider — openai async client, tool_calling
    │   ├── anthropic.py       # AnthropicProvider — anthropic client, tool_use format
    │   ├── google.py          # GoogleProvider — google-generativeai, function declarations
    │   ├── groq.py            # GroqProvider — extends OpenAiProvider with Groq base_url
    │   └── ollama.py          # OllamaProvider — local OpenAI-compatible endpoint
    │
    ├── realtime/              # WebSocket + Redis pub/sub infrastructure
    │   ├── __init__.py
    │   ├── manager.py         # ConnectionManager — WS registry, Redis listener, message routing
    │   └── events.py          # broadcast_agent_status(), broadcast_task_event(), etc.
    │
    ├── core/                  # Shared utilities used across the app
    │   ├── deps.py            # FastAPI Depends: get_session, get_current_user, get_ws_manager
    │   ├── security.py        # create_access_token(), verify_token(), hash_password()
    │   ├── logging.py         # structlog configuration — JSON in prod, colored in dev
    │   └── exceptions.py      # Custom exceptions + FastAPI exception handlers
    │
    └── seeds/                 # Initial data loaders (run once after migration)
        ├── __init__.py
        ├── agent_classes.py   # Inserts 17 predefined AgentClass records
        └── admin_user.py      # Creates initial admin user from env vars
```

### Key File Details

#### `app/main.py`
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.realtime.manager import ws_manager
from app.routers import agents, agent_classes, tasks, tools, llm_configs, chat, memory, system, websocket, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await ws_manager.startup()
    yield
    # Shutdown
    await ws_manager.shutdown()


app = FastAPI(
    title="Qubot API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(agents.router, prefix=API_PREFIX)
app.include_router(agent_classes.router, prefix=API_PREFIX)
app.include_router(tasks.router, prefix=API_PREFIX)
app.include_router(tools.router, prefix=API_PREFIX)
app.include_router(llm_configs.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(memory.router, prefix=API_PREFIX)
app.include_router(system.router, prefix=API_PREFIX)
app.include_router(websocket.router)   # /ws — no prefix
```

#### `app/worker.py`
```python
"""
Qubot Worker Process
Run standalone: python -m app.worker
Consumes Redis Streams, executes agent tasks.
"""
import asyncio
import signal
from app.services.execution_service import ExecutionService
from app.config import settings
from app.core.logging import configure_logging

configure_logging()

async def main():
    service = ExecutionService()
    loop = asyncio.get_event_loop()

    def shutdown(sig):
        print(f"Worker shutdown signal: {sig}")
        service.stop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: shutdown(s))

    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
```

#### `app/database.py`
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with async_session_factory() as session:
        yield session

async def create_tables():
    """Only for testing. Production uses Alembic migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

#### `app/redis_client.py`
```python
import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        await _redis.ping()
    return _redis

async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
```

---

## Frontend

```
frontend/
├── Dockerfile                 # Multi-stage Node 20 build → Alpine runtime
├── next.config.js             # output: 'standalone', image domains, rewrites
├── tailwind.config.js         # Theme: Qubot color tokens, dark mode class
├── tsconfig.json              # strict: true, paths: { "@/*": ["./"] }
├── package.json               # All dependencies (see frontend-architecture.md)
├── .eslintrc.json             # Next.js + TypeScript rules
│
├── public/
│   ├── sprites/               # Agent SVG sprites by class slug
│   │   ├── software-engineer.svg
│   │   ├── devops-engineer.svg
│   │   ├── data-scientist.svg
│   │   ├── security-analyst.svg
│   │   ├── financial-analyst.svg
│   │   └── ...                # One per predefined AgentClass
│   └── office/
│       ├── floor-tile.svg     # Desk/floor tile SVG
│       └── desk.svg           # Office desk SVG
│
├── app/                       # Next.js App Router
│   ├── layout.tsx             # Root layout: fonts, ThemeProvider, WebSocketProvider, QueryClientProvider
│   ├── page.tsx               # Redirect → /dashboard
│   ├── globals.css            # Tailwind base + CSS custom properties
│   │
│   ├── dashboard/
│   │   └── page.tsx           # Coworking office view (CoworkingCanvas + ActivityFeed sidebar)
│   │
│   ├── mission-control/
│   │   └── page.tsx           # Kanban board (4-column task management)
│   │
│   ├── agents/
│   │   ├── page.tsx           # Agent list with search/filter + status badges
│   │   ├── new/
│   │   │   └── page.tsx       # 6-step agent creation wizard
│   │   └── [id]/
│   │       └── page.tsx       # Agent detail: config, tools, memory, task history
│   │
│   ├── chat/
│   │   └── page.tsx           # Orchestrator chat interface
│   │
│   ├── tools/
│   │   ├── page.tsx           # Tool registry list
│   │   └── [id]/
│   │       └── page.tsx       # Tool detail/edit
│   │
│   └── settings/
│       ├── llm/
│       │   └── page.tsx       # LLM config management (providers, models, test connectivity)
│       └── memory/
│           └── page.tsx       # Global memory management (CRUD)
│
├── components/
│   │
│   ├── coworking/             # Konva.js office canvas
│   │   ├── CoworkingCanvas.tsx    # Konva Stage wrapper, ResizeObserver, Layer tree
│   │   ├── OfficeFloor.tsx        # Checkerboard tiles using Rect or SVG image
│   │   ├── AgentSprite.tsx        # Konva Group: sprite image, status dot, name label, domain badge
│   │   ├── AgentDesk.tsx          # Desk surface + monitor + AgentSprite positioned
│   │   ├── StatusBubble.tsx       # Animated thought bubble shown when WORKING
│   │   └── ActivityParticles.tsx  # Konva animation: floating particles on WORKING agents
│   │
│   ├── kanban/
│   │   ├── KanbanBoard.tsx        # DndContext wrapper, columns layout
│   │   ├── KanbanColumn.tsx       # SortableContext for one status column
│   │   ├── TaskCard.tsx           # Draggable task card: title, priority badge, agent avatar
│   │   └── TaskDetail.tsx         # Task detail sheet: description, event timeline, comments
│   │
│   ├── agents/
│   │   ├── AgentCard.tsx          # Agent summary card: sprite, name, class, status, current task
│   │   ├── AgentBadge.tsx         # Compact: mini avatar + name + colored status dot
│   │   ├── AgentStatusIndicator.tsx  # Large status icon + label (IDLE/WORKING/ERROR/OFFLINE)
│   │   └── AgentCreationWizard/
│   │       ├── WizardShell.tsx        # Step progress bar, Back/Next/Submit buttons, preview panel
│   │       ├── Step1Domain.tsx        # 8 domain cards (TECH, FINANCE, HR, etc.)
│   │       ├── Step2Class.tsx         # Filtered class cards for selected domain + custom class option
│   │       ├── Step3Identity.tsx      # Name input, gender selector, avatar color pickers
│   │       ├── Step4Personality.tsx   # TraitSlider × 3 + TagInput for strengths/weaknesses
│   │       ├── Step5LlmConfig.tsx     # LlmConfig dropdown + create new inline
│   │       └── Step6Tools.tsx         # Tool checklist with permission level selectors
│   │
│   ├── chat/
│   │   ├── ChatWindow.tsx         # Full chat UI: message history + input bar
│   │   ├── ChatMessage.tsx        # Renders user vs assistant messages; markdown support
│   │   └── ActionChips.tsx        # Visual chips: "Created task X", "Assigned to Agent Y"
│   │
│   ├── activity/
│   │   └── ActivityFeed.tsx       # Fixed sidebar: real-time log with agent avatars + links
│   │
│   ├── tools/
│   │   ├── ToolCard.tsx           # Tool summary: name, type badge, description
│   │   └── ToolFormModal.tsx      # Create/edit tool: type-aware dynamic config fields
│   │
│   ├── memory/
│   │   ├── MemoryCard.tsx         # Global memory entry: key, content preview, tags, edit/delete
│   │   └── MemoryForm.tsx         # Create/edit global memory: key, content, content_type, tags
│   │
│   ├── shared/
│   │   ├── DomainBadge.tsx        # Colored pill: domain name + icon
│   │   ├── PriorityBadge.tsx      # Colored pill: LOW/MEDIUM/HIGH/CRITICAL
│   │   ├── StatusBadge.tsx        # Colored pill for task or agent status
│   │   ├── AgentAvatar.tsx        # Sprite image with fallback initials, size variants
│   │   ├── ConfirmDialog.tsx      # Reusable delete confirmation modal
│   │   ├── LoadingSpinner.tsx     # Centered spinner with optional label
│   │   └── EmptyState.tsx         # Illustration + message + optional CTA button
│   │
│   └── ui/                    # Shadcn/ui re-exports (Button, Card, Dialog, Input, etc.)
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── input.tsx
│       ├── select.tsx
│       ├── badge.tsx
│       ├── sheet.tsx
│       ├── toast.tsx
│       └── ...
│
├── lib/
│   ├── api.ts                 # Typed fetch client with envelope unwrapping, error handling
│   ├── websocket.ts           # Socket.io singleton with event bus + auto-reconnect
│   └── utils.ts               # cn() className merge, formatDate, truncate, domainColors
│
├── store/
│   ├── agents.store.ts        # Zustand: agents map, selectedAgentId, update from WS events
│   ├── tasks.store.ts         # Zustand: tasks map, status columns for Kanban, update from WS
│   └── activity.store.ts      # Zustand: feed entries (capped at 100), append on WS event
│
├── hooks/
│   ├── useAgents.ts           # TanStack Query: useAgents(), useAgent(id), useCreateAgent(), useUpdateAgent()
│   ├── useTasks.ts            # TanStack Query: useTasks(), useTask(id), useUpdateTaskStatus()
│   ├── useTools.ts            # TanStack Query: useTools(), useCreateTool(), useTestTool()
│   ├── useLlmConfigs.ts       # TanStack Query: useLlmConfigs(), useTestLlmConfig()
│   ├── useMemory.ts           # TanStack Query: useGlobalMemory(), useCreateMemory()
│   ├── useWebSocket.ts        # Initialize WS, subscribe to channels, dispatch to stores
│   └── useActivityFeed.ts     # Read from activity.store, provides formatted entries
│
└── types/
    └── index.ts               # TypeScript interfaces mirroring backend schemas:
                               # Agent, AgentClass, Task, TaskEvent, Tool, LlmConfig,
                               # GlobalMemory, AgentMemory, TaskMemory, WsEvent,
                               # ChatRequest, ChatResponse, OrchestratorAction, etc.
```

---

## Nginx

```
nginx/
├── nginx.conf          # Development HTTP proxy (localhost)
└── nginx.prod.conf     # Production HTTPS with SSL termination, security headers
```

---

## Documentation

```
docs/
├── idea.md                    # Original concept (source material, read-only)
├── idea1.md                   # Second concept document (source material, read-only)
├── architecture.md            # System overview, C4 diagrams, ADRs
├── database-schema.md         # All SQLModel models, enums, indexes, migrations
├── api-specification.md       # All REST endpoints + WebSocket events
├── frontend-architecture.md   # Next.js structure, Konva.js, components, stores
├── agent-orchestration.md     # Orchestrator, execution loop, assignment algorithm
├── llm-integration.md         # Provider abstraction, cost tracking, retry logic
├── tools-system.md            # Tool registry, implementations, permissions
├── memory-system.md           # Memory types, context injection, vector DB prep
├── realtime-system.md         # WebSocket architecture, Redis pub/sub, events
├── deployment.md              # Docker, docker-compose, Nginx, VPS setup, Dokploy
├── project-structure.md       # This file — complete directory tree
└── implementation-roadmap.md  # 6-phase build plan with specific tasks
```

---

## Root Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Development environment — all services with hot reload, exposed ports |
| `docker-compose.prod.yml` | Production overrides — no exposed DB/Redis, nginx, resource limits |
| `.env.example` | Template for all required environment variables with comments |
| `.gitignore` | Ignores `.env`, `__pycache__`, `.next/`, `node_modules/`, `*.pyc` |
| `README.md` | Quick start guide, links to docs |

### `.gitignore`

```gitignore
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
dist/
build/
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage

# Next.js
frontend/.next/
frontend/out/
frontend/node_modules/

# System
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp

# Docker volumes (if accidentally created locally)
postgres_data/
redis_data/
```

---

## Module Dependency Map

```
app/main.py
  └── routers/*
        └── services/*
              ├── database.py (get_session)
              ├── redis_client.py (get_redis)
              ├── models/* (SQLModel tables)
              ├── llm/registry.py → llm/*.py (providers)
              ├── tools_impl/registry.py → tools_impl/*.py
              ├── realtime/events.py → realtime/manager.py
              └── memory_service.py

app/worker.py
  └── services/execution_service.py
        ├── llm/registry.py
        ├── tools_impl/registry.py
        ├── services/memory_service.py
        └── realtime/events.py (broadcast updates)
```

---

## Naming Conventions Summary

| Layer | Convention | Example |
|-------|-----------|---------|
| DB tables | snake_case (auto from class) | `agent_memory` |
| Model classes | PascalCase | `AgentMemory` |
| Schema classes | PascalCase + suffix | `AgentMemoryRead`, `AgentCreate` |
| Router files | snake_case | `agent_classes.py` |
| Router prefixes | kebab-case | `/agent-classes` |
| Service classes | PascalCase + `Service` | `AssignmentService` |
| Tool classes | PascalCase + `Tool` | `HttpApiTool` |
| Provider classes | PascalCase + `Provider` | `AnthropicProvider` |
| Frontend components | PascalCase | `AgentDesk.tsx` |
| Frontend hooks | camelCase + `use` | `useAgents.ts` |
| Frontend stores | camelCase + `.store` | `agents.store.ts` |
| Env vars | UPPER_SNAKE_CASE | `POSTGRES_PASSWORD` |
