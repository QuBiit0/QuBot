# Qubot — Implementation Roadmap

> **6-phase build plan** — from empty repo to production deployment.
> Each phase produces working, testable software. Phases are sequential; complete Phase N before starting Phase N+1.

---

## Phase Overview

| Phase | Name | Deliverable | Duration |
|-------|------|-------------|---------|
| 1 | Backend Foundation | Working REST API + database | Week 1–2 |
| 2 | Frontend Mission Control | Functional Kanban + agent management UI | Week 2–3 |
| 3 | Coworking Visual Layer | Gamified canvas with animated agents | Week 3–4 |
| 4 | Agent Creation + Tool Editor | Complete no-code configuration UI | Week 4–5 |
| 5 | Orchestrator + Agent Execution | Real AI agents performing tasks | Week 5–7 |
| 6 | Polish + Memory + Production | Production-ready, tested, deployed | Week 7–9 |

---

## Phase 1 — Backend Foundation

**Goal**: Working REST API with full CRUD and authenticated access. No LLM calls yet — just the data layer and HTTP layer.

### 1.1 Project Scaffolding

- [ ] Create directory structure per `docs/project-structure.md`
- [ ] Initialize `backend/` with `pyproject.toml` (ruff, mypy config)
- [ ] Create `requirements.txt` with all pinned dependencies
- [ ] Configure `structlog` in `app/core/logging.py` — colored in dev, JSON in prod
- [ ] Create `app/config.py` with `Settings(BaseSettings)` — all env vars
- [ ] Create `.env.example` with all required variables documented

### 1.2 Database Layer

- [ ] Create `app/database.py` — async SQLAlchemy engine, `async_session_factory`, `get_session()`
- [ ] Create `app/models/enums.py` — all 9 enums (DomainEnum, GenderEnum, AgentStatusEnum, TaskStatusEnum, PriorityEnum, ToolTypeEnum, LlmProviderEnum, PermissionEnum, TaskEventTypeEnum)
- [ ] Create `app/models/agent.py` — `AgentClass`, `Agent`, `AgentTool` SQLModel classes
- [ ] Create `app/models/task.py` — `Task`, `TaskEvent` SQLModel classes
- [ ] Create `app/models/tool.py` — `Tool` SQLModel class
- [ ] Create `app/models/llm.py` — `LlmConfig`, `LlmCallLog` SQLModel classes
- [ ] Create `app/models/memory.py` — `GlobalMemory`, `AgentMemory`, `TaskMemory` SQLModel classes
- [ ] Create `app/models/__init__.py` — re-export all models for Alembic
- [ ] Configure Alembic: `alembic.ini`, `alembic/env.py` (async), `alembic/script.py.mako`
- [ ] Generate and run first migration: `alembic revision --autogenerate -m "initial_schema"`
- [ ] Verify migration creates all 12 tables with correct indexes

### 1.3 Redis

- [ ] Create `app/redis_client.py` — async Redis singleton with ping health check
- [ ] Test connection in startup lifespan

### 1.4 Auth

- [ ] Create `app/core/security.py` — `create_access_token()`, `verify_token()`, `hash_password()`, `verify_password()`
- [ ] Create `app/routers/auth.py` — `POST /auth/login`, `POST /auth/refresh`
- [ ] Create `app/core/deps.py` — `get_session`, `get_current_user` FastAPI dependencies

### 1.5 Schemas

- [ ] Create `app/schemas/agent.py` — `AgentRead`, `AgentCreate`, `AgentUpdate`, `AgentDetail`, `AgentClassRead`, `AgentClassCreate`
- [ ] Create `app/schemas/task.py` — `TaskRead`, `TaskCreate`, `TaskUpdate`, `TaskDetail`, `TaskEventRead`
- [ ] Create `app/schemas/tool.py` — `ToolRead`, `ToolCreate`, `ToolUpdate`
- [ ] Create `app/schemas/llm.py` — `LlmConfigRead`, `LlmConfigCreate`, `LlmConfigUpdate`
- [ ] Create `app/schemas/memory.py` — `GlobalMemoryRead`, `GlobalMemoryCreate`, `AgentMemoryRead`
- [ ] Create `app/schemas/chat.py` — `ChatRequest`, `ChatResponse`, `OrchestratorAction`

### 1.6 Services

- [ ] Create `app/services/agent_service.py` — full CRUD + status updates + memory retrieval
- [ ] Create `app/services/task_service.py` — full CRUD + state machine validation + `create_task_event()`
- [ ] Create `app/services/tool_service.py` — full CRUD + agent-tool assignment
- [ ] Create `app/services/llm_service.py` — CRUD only (no provider calls yet)

### 1.7 Routers

- [ ] Create `app/routers/agents.py` — all 8 agent endpoints
- [ ] Create `app/routers/agent_classes.py` — all 4 endpoints
- [ ] Create `app/routers/tasks.py` — all 8 task endpoints
- [ ] Create `app/routers/tools.py` — all 6 tool endpoints (test endpoint returns stub)
- [ ] Create `app/routers/llm_configs.py` — all 5 endpoints (test endpoint returns stub)
- [ ] Create `app/routers/memory.py` — 3 global memory endpoints
- [ ] Create `app/routers/system.py` — `/health` with real DB + Redis checks, `/stats` stub
- [ ] Wire all routers in `app/main.py` with CORS middleware

### 1.8 Seed Data

- [ ] Create `app/seeds/agent_classes.py` — insert all 17 predefined `AgentClass` records with correct avatar_config, domain, description
- [ ] Create `app/seeds/admin_user.py` — create admin user from `ADMIN_EMAIL`/`ADMIN_PASSWORD` env vars
- [ ] Register seeds as CLI commands runnable via `python -m app.seeds.*`

### 1.9 Docker

- [ ] Write `backend/Dockerfile` (multi-stage, non-root user)
- [ ] Write `docker-compose.yml` with postgres, redis, api services
- [ ] Verify `docker compose up` starts all services successfully
- [ ] Verify `docker compose exec api alembic upgrade head` succeeds
- [ ] Verify `/api/v1/system/health` returns `{"status":"healthy",...}`

### 1.10 Tests

- [ ] Create `tests/conftest.py` — async test client using TestClient, isolated test DB session
- [ ] `tests/integration/test_agents_api.py` — test create, list, get, update, delete agent
- [ ] `tests/integration/test_tasks_api.py` — test create, list, status transitions
- [ ] `tests/unit/test_assignment_service.py` — test scoring algorithm edge cases

**Phase 1 Exit Criteria:**
- All REST endpoints return correct status codes and response shapes
- `pytest` passes with >80% coverage
- `ruff check .` passes with zero errors
- `docker compose up` starts cleanly from fresh clone

---

## Phase 2 — Frontend Mission Control Basics

**Goal**: Usable management UI with Kanban board, agent list, and live WebSocket updates. No visual canvas yet — focus on functionality.

### 2.1 Next.js Setup

- [ ] Create `frontend/` with `next.config.js` (`output: 'standalone'`)
- [ ] Configure TypeScript strict mode, Tailwind, Shadcn/ui
- [ ] Create `types/index.ts` — all TypeScript interfaces matching backend schemas
- [ ] Configure `lib/api.ts` — typed fetch client with base URL, auth header injection, envelope unwrapping

### 2.2 WebSocket Client

- [ ] Create `lib/websocket.ts` — Socket.io (or native WS) singleton with reconnect logic, event bus
- [ ] Create `hooks/useWebSocket.ts` — initialize connection, wire events to Zustand stores
- [ ] Create `store/agents.store.ts` — agents map, update from `agent_status_changed` WS events
- [ ] Create `store/tasks.store.ts` — tasks map, update from `task_status_changed` WS events
- [ ] Create `store/activity.store.ts` — feed entries, append on `activity_feed` WS events

> **Backend prerequisite**: Implement WebSocket endpoint before this step.
>
> - [ ] Create `app/realtime/manager.py` — `ConnectionManager` with Redis pub/sub subscriber
> - [ ] Create `app/realtime/events.py` — all broadcast helper functions
> - [ ] Create `app/routers/websocket.py` — `/ws?token=...` endpoint

### 2.3 TanStack Query Hooks

- [ ] `hooks/useAgents.ts` — `useAgents()`, `useAgent(id)`, `useCreateAgent()`, `useUpdateAgent()`, `useDeleteAgent()`
- [ ] `hooks/useTasks.ts` — `useTasks()`, `useTask(id)`, `useUpdateTaskStatus()` with optimistic updates
- [ ] `hooks/useTools.ts` — `useTools()`, `useCreateTool()`
- [ ] `hooks/useLlmConfigs.ts` — `useLlmConfigs()`

### 2.4 Kanban Board

- [ ] Create `components/kanban/KanbanBoard.tsx` — dnd-kit `DndContext`, 4 columns (BACKLOG, IN_PROGRESS, IN_REVIEW, DONE)
- [ ] Create `components/kanban/KanbanColumn.tsx` — `SortableContext`, column header with task count
- [ ] Create `components/kanban/TaskCard.tsx` — draggable, shows title, priority badge, assignee avatar
- [ ] Create `components/kanban/TaskDetail.tsx` — Sheet panel: full task info, event timeline, add comment
- [ ] Wire drag end: call `PATCH /tasks/{id}/status`, update Zustand store optimistically
- [ ] Wire WebSocket `task_status_changed`: auto-move cards without user action
- [ ] Create `app/mission-control/page.tsx` — full Kanban page with filter controls

### 2.5 Agent List

- [ ] Create `components/agents/AgentCard.tsx` — avatar, name, class, domain badge, status indicator
- [ ] Create `components/agents/AgentBadge.tsx` — compact inline badge
- [ ] Create `components/agents/AgentStatusIndicator.tsx` — large icon + label
- [ ] Create `app/agents/page.tsx` — searchable/filterable agent grid
- [ ] Create `app/agents/[id]/page.tsx` — detail page: config tabs, tools list, memory entries, task history table

### 2.6 Activity Feed

- [ ] Create `components/activity/ActivityFeed.tsx` — fixed right panel, reads from `activity.store`, auto-scroll with pause-on-hover
- [ ] Integrate into root `app/layout.tsx` or `dashboard` page

### 2.7 Settings Pages

- [ ] Create `app/settings/llm/page.tsx` — list LLM configs, create/edit form, "Test Connection" button
- [ ] Create `app/settings/memory/page.tsx` — list GlobalMemory entries, create/edit/delete

### 2.8 Docker Frontend

- [ ] Write `frontend/Dockerfile` (multi-stage, standalone output)
- [ ] Add `frontend` service to `docker-compose.yml`
- [ ] Verify full stack runs: `docker compose up` → `localhost:3000` shows Kanban

**Phase 2 Exit Criteria:**
- Kanban board shows tasks, supports drag & drop, auto-updates via WebSocket
- Agents page shows all agents with correct status badges
- Activity feed shows real-time events
- Settings pages allow LLM config and global memory management

---

## Phase 3 — Coworking Visual Layer

**Goal**: Visual coworking office with animated agent sprites. Agents must animate based on real status from the backend.

### 3.1 Canvas Infrastructure

- [ ] Add Konva.js to frontend dependencies (`konva`, `react-konva`)
- [ ] Create `components/coworking/CoworkingCanvas.tsx` — Konva Stage with 3 Layers (floor, agents, effects), ResizeObserver for responsive sizing

### 3.2 Office Floor

- [ ] Create `components/coworking/OfficeFloor.tsx` — checkerboard tile pattern using Konva `Rect` grid
- [ ] Add desk SVG images loaded as Konva `Image` nodes
- [ ] Define desk position grid in canvas coordinates (e.g., 4 columns × N rows based on agent count)

### 3.3 Agent Sprites

- [ ] Add SVG sprite files to `public/sprites/` — one per AgentClass slug (use placeholder silhouettes initially)
- [ ] Create `components/coworking/AgentSprite.tsx` — Konva Group containing:
  - Body image (sprite SVG, tinted with `agent.avatar_config.color_primary`)
  - Status dot (Circle with shadow, color maps to status)
  - Name label (Text node below sprite)
  - Domain badge (small colored circle with icon)
- [ ] Implement status animations via `Konva.Animation`:
  - `IDLE`: slow scale pulse (1.0 → 1.02 → 1.0, 3s loop)
  - `WORKING`: fast scale pulse (1.0 → 1.05 → 1.0, 0.8s loop) + monitor glow on desk
  - `ERROR`: red shake (oscillating X offset) + red status dot
  - `OFFLINE`: desaturated filter (set `opacity: 0.4`)

### 3.4 Agent Desk

- [ ] Create `components/coworking/AgentDesk.tsx` — combines desk image + monitor (Rect + glow) + AgentSprite
- [ ] Monitor glow: yellow/green `shadowBlur` on monitor Rect, animated during WORKING

### 3.5 Status Bubble

- [ ] Create `components/coworking/StatusBubble.tsx` — thought bubble Konva Group above agent
- [ ] Show truncated current task title (30 chars) when WORKING
- [ ] Fade in/out via Konva tween when status changes

### 3.6 Click Interaction

- [ ] On agent sprite click: set `selectedAgentId` in Zustand store
- [ ] Slide-in `Sheet` panel from right with full agent detail (reuse component from Phase 2)

### 3.7 Dashboard Layout

- [ ] Create `app/dashboard/page.tsx` — split layout: CoworkingCanvas (center, ~75% width) + ActivityFeed (right sidebar, ~25%)
- [ ] Navigation: top navbar with links to Dashboard, Mission Control, Agents, Chat, Settings
- [ ] Connect WebSocket `agent_status_changed` → update agent in store → Konva re-renders

**Phase 3 Exit Criteria:**
- All agents appear as sprites on office floor
- Status animations play correctly for IDLE/WORKING/ERROR/OFFLINE
- Clicking an agent shows detail panel
- Dashboard looks like a recognizable "coworking office" visual

---

## Phase 4 — Agent Creation Wizard + Tool Editor

**Goal**: Complete no-code configuration UI. Users can create any agent and any tool entirely through the UI.

### 4.1 Agent Creation Wizard

- [ ] Create `components/agents/AgentCreationWizard/WizardShell.tsx` — step progress bar (6 steps), Back/Next/Submit buttons, right-side live avatar preview panel
- [ ] `Step1Domain.tsx` — 8 domain selection cards with icons, descriptions
- [ ] `Step2Class.tsx` — filtered class cards for selected domain; "+ Create Custom Class" button opens inline modal
- [ ] `Step3Identity.tsx` — text input for agent name, gender radio buttons, color pickers for `color_primary`/`color_secondary`, sprite preview
- [ ] `Step4Personality.tsx` — `TraitSlider` for detail_oriented, risk_tolerance, formality; `TagInput` for strengths and weaknesses
- [ ] `Step5LlmConfig.tsx` — `<Select>` of existing LlmConfigs; "+ Create New" button opens quick-create form (provider, model_name, api_key_ref)
- [ ] `Step6Tools.tsx` — checkbox list of all tools; permission level dropdown per selected tool (READ_ONLY/READ_WRITE/DANGEROUS)
- [ ] Wire form state accumulation across steps; on Submit call `POST /agents`

### 4.2 Custom Class Creation

- [ ] Create inline `CustomClassModal.tsx` — name, description, domain (pre-filled), avatar icon picker
- [ ] After creation: automatically select the new class in Step 2

### 4.3 Agent Editing

- [ ] Reuse WizardShell in edit mode: pre-fill all steps from `agent.data`
- [ ] Wire Submit to `PUT /agents/{id}`
- [ ] Add "Edit Agent" button on `app/agents/[id]/page.tsx`

### 4.4 Tool Registry

- [ ] Create `components/tools/ToolCard.tsx` — name, type badge (colored), description truncated, edit/delete buttons
- [ ] Create `components/tools/ToolFormModal.tsx` — dialog with tool type selector; shows type-specific config fields:
  - `HTTP_API`: base_url, auth_type, default_headers textarea
  - `SYSTEM_SHELL`: allowed_commands textarea, working_directory, timeout
  - `WEB_BROWSER`: timeout, max_content_length
  - `FILESYSTEM`: base_directory, allowed_extensions, max_file_size
  - `SCHEDULER`: (no extra config)
  - `CUSTOM`: config JSON textarea, input_schema JSON textarea
- [ ] Add "Test Tool" button: calls `POST /tools/{id}/test` with sample input, shows result modal

### 4.5 LLM Config Manager

- [ ] Create `LlmConfigCard.tsx` — provider badge, model name, temperature, test connectivity button
- [ ] Create `LlmConfigForm.tsx` — full form: provider select, model_name, temperature, top_p, max_tokens, api_key_ref
- [ ] "Test Connection" button: calls `POST /llm-configs/{id}/test`, shows latency or error

**Phase 4 Exit Criteria:**
- Any user can create a custom agent through the wizard without touching code
- All 6 tool types can be created and configured through the UI
- LLM configs can be created and tested

---

## Phase 5 — Orchestrator + Agent Execution

**Goal**: Real AI agents executing tasks with tool-calling. End-to-end: user sends chat message → orchestrator creates task → worker agent executes → result visible in UI.

### 5.1 LLM Provider Implementations

- [ ] Create `app/llm/base.py` — `BaseLlmProvider`, `LlmMessage`, `LlmResponse`, `LlmUsage`, `LlmToolCall`
- [ ] Create `app/llm/registry.py` — `PROVIDERS` dict, `get_provider(config)` factory
- [ ] Create `app/llm/openai.py` — `OpenAiProvider`: async client, message format, tool_calls parsing, cost calculation
- [ ] Create `app/llm/anthropic.py` — `AnthropicProvider`: tool_use format, content block parsing
- [ ] Create `app/llm/groq.py` — `GroqProvider` (subclasses OpenAiProvider with Groq base_url)
- [ ] Create `app/llm/ollama.py` — `OllamaProvider` (local, cost_usd=0)
- [ ] Create `app/llm/google.py` — `GoogleProvider`: function declarations format, candidate parsing
- [ ] Update `app/services/llm_service.py` — `complete_with_retry()` with tenacity, `LlmCallLog` write

### 5.2 Tool Implementations

- [ ] Create `app/tools_impl/base.py` — `BaseTool` ABC, `ToolResult` model
- [ ] Create `app/tools_impl/registry.py` — `get_tool_impl(tool: Tool) → BaseTool` factory
- [ ] Create `app/tools_impl/http_api.py` — `HttpApiTool` with domain whitelist, auth types, env var resolution
- [ ] Create `app/tools_impl/shell.py` — `SystemShellTool` with command whitelist, dangerous pattern blacklist, asyncio subprocess timeout
- [ ] Create `app/tools_impl/browser.py` — `WebBrowserTool` with httpx + BeautifulSoup4, extract modes, content size limit
- [ ] Create `app/tools_impl/filesystem.py` — `FilesystemTool` with path traversal protection, extension allowlist
- [ ] Create `app/tools_impl/scheduler.py` — `SchedulerTool` creates future Task in DB
- [ ] Create `app/tools_impl/memory_write.py` — `MemoryWriteTool` writes to AgentMemory
- [ ] Update `app/routers/tools.py` `POST /tools/{id}/test` — execute real tool with sample input

### 5.3 Orchestrator Service

- [ ] Create `app/services/orchestrator_service.py`:
  - `build_orchestrator_context()` — fetches all agents + recent tasks, formats as prompt section
  - `handle_chat()` — find/verify orchestrator agent, build system prompt, call LLM, parse JSON response
  - `execute_orchestrator_actions()` — handles CREATE_TASK, ASSIGN_TASK, UPDATE_TASK actions
- [ ] Update `app/routers/chat.py` — wire `POST /chat` to `orchestrator_service.handle_chat()`
- [ ] Store chat messages in Redis list (`chat:history`) with 50-message cap

### 5.4 Assignment Service

- [ ] Create `app/services/assignment_service.py`:
  - `find_best_agent(task)` — scoring: base 100, domain +15, class_match +25, current_task -20, ERROR status -30
  - Filter out OFFLINE agents
  - Return highest scoring available agent

### 5.5 Worker Process + Execution Service

- [ ] Create `app/services/execution_service.py`:
  - `start()` / `stop()` lifecycle with Redis Streams XREADGROUP consumer
  - `execute_task(agent, task)` — full tool-calling loop (max 20 iterations):
    1. Build system prompt with memory context
    2. Call LLM provider
    3. On `tool_calls`: execute each tool, create `TaskEvent(TOOL_CALL)`, append to messages
    4. On `stop`: parse final response `{status, summary/reason}`
    5. Update task status + agent status
    6. Broadcast WebSocket events after each step
  - `_build_system_prompt(agent, task)` — personality + tools + memory injection
  - `_parse_final_response(content)` — JSON extraction with regex fallback
- [ ] Create `app/worker.py` — standalone entry point (asyncio.run)
- [ ] Add `worker` service to `docker-compose.yml`

### 5.6 Memory Service

- [ ] Create `app/services/memory_service.py`:
  - `get_global_memories()` with JSONB tag filter + SQL LIKE search
  - `get_agent_memories()` sorted by importance desc, updates `last_accessed`
  - `write_agent_memory()` upsert by (agent_id, key)
  - `build_agent_context()` — combines global + agent + task memories into prompt string
  - `generate_task_memory()` — post-task LLM summarization, saves `TaskMemory`

### 5.7 Chat UI

- [ ] Create `components/chat/ChatWindow.tsx` — message list + sticky input bar
- [ ] Create `components/chat/ChatMessage.tsx` — renders user vs assistant messages (markdown via `react-markdown`)
- [ ] Create `components/chat/ActionChips.tsx` — visual chips for each orchestrator action (e.g., "Created task: Write Report" with task link)
- [ ] Create `app/chat/page.tsx` — full-screen chat page
- [ ] Connect to `POST /chat`, show streaming-style response + action chips

### 5.8 End-to-End Test

- [ ] Manual test: Send "Research the latest AI news and create a summary report" in chat
  - Orchestrator should: create task, assign to a TECH agent
  - Worker should: pick up task, call web browser tool, produce summary
  - UI should: show task appear in Kanban, agent animate as WORKING, task move to DONE, task memory saved
- [ ] `tests/integration/test_chat_api.py` — mock LLM provider, verify action parsing

**Phase 5 Exit Criteria:**
- `/chat` endpoint correctly creates tasks and assigns agents
- Worker process picks up tasks and executes tool-calling loops
- Agents animate as WORKING while tasks run, return to IDLE when done
- Task events appear in Kanban task detail timeline
- Activity feed shows real-time progress

---

## Phase 6 — Polish, Memory, Advanced Features

**Goal**: Production-ready system — polished UI, complete memory system, full test suite, deployed to VPS.

### 6.1 Visual Polish

- [ ] Add `components/coworking/ActivityParticles.tsx` — Konva animation: small particles float upward from WORKING agents
- [ ] Smooth agent status transitions with Konva tweens (fade, scale)
- [ ] Add `StatusBubble` thought bubbles with task title truncated to 30 chars
- [ ] Framer Motion: page transition animations, card hover effects, wizard step transitions
- [ ] Responsive layout: canvas shrinks gracefully at tablet widths; mobile shows list fallback

### 6.2 Kanban Improvements

- [ ] Filter bar: by domain, by assigned agent, by priority
- [ ] Bulk operations: select multiple tasks → bulk assign, bulk delete
- [ ] Task creation from Kanban: "+ New Task" button in BACKLOG column opens quick-create form
- [ ] Priority color-coded left border on task cards

### 6.3 Memory UI

- [ ] Agent detail page: tab for "Memory" — list `AgentMemory` entries with importance badges, delete button
- [ ] Memory importance visualization: 5 = red badge, 4 = orange, 3 = yellow, 1-2 = gray
- [ ] Global memory search: full-text search input on `/settings/memory` page
- [ ] TaskMemory view: on task detail, show "Task Summary" section if TaskMemory exists

### 6.4 System Stats Dashboard

- [ ] Implement `GET /system/stats`:
  ```json
  {
    "agents": { "total": 12, "idle": 8, "working": 3, "error": 1 },
    "tasks": { "backlog": 5, "in_progress": 3, "done_today": 12, "failed_today": 1 },
    "llm_costs": { "today_usd": 1.23, "this_month_usd": 45.67, "total_calls": 1234 }
  }
  ```
- [ ] Create stats widget cards on dashboard sidebar or separate `/stats` page

### 6.5 Subtask Support

- [ ] Orchestrator can create tasks with `parent_task_id` for multi-step workflows
- [ ] Task detail shows subtask list with progress indicator
- [ ] Kanban filter option: "Show parent tasks only"

### 6.6 Test Suite Completion

- [ ] `tests/unit/test_assignment_service.py` — 10+ scenarios: no agents, all offline, tie-breaking
- [ ] `tests/unit/test_orchestrator_service.py` — action parsing: valid JSON, JSON in code block, partial JSON, no JSON
- [ ] `tests/unit/test_tool_executor.py` — permission enforcement, timeout, dangerous tool blocked
- [ ] `tests/unit/test_memory_service.py` — context building, importance ordering, tag filtering
- [ ] `tests/integration/test_agents_api.py` — full CRUD, status transitions, memory endpoints
- [ ] `tests/integration/test_tasks_api.py` — full lifecycle, invalid transitions rejected, event log grows
- [ ] `tests/integration/test_chat_api.py` — mock LLM, verify actions executed, tasks created
- [ ] `tests/integration/test_tools_api.py` — tool CRUD, test execution with sandbox
- [ ] Achieve >80% overall coverage, >90% on services

### 6.7 Production Deployment

- [ ] Write `docker-compose.prod.yml` with nginx service, no exposed DB/Redis ports
- [ ] Write `nginx/nginx.prod.conf` with HTTPS, security headers, WebSocket upgrade
- [ ] Configure SSL with Let's Encrypt certbot
- [ ] Set all production env vars (strong passwords, real API keys)
- [ ] Run on VPS: fresh Ubuntu 22.04 → docker install → clone → deploy
- [ ] Verify `GET /api/v1/system/health` returns healthy in production
- [ ] Set up certbot cron for SSL renewal

### 6.8 Documentation Finalization

- [ ] Verify all 12 spec documents are complete and accurate vs implemented code
- [ ] Write `README.md` with quick-start, local dev setup, deployment instructions
- [ ] Add OpenAPI descriptions to all FastAPI route docstrings (auto-generates `/api/docs`)

**Phase 6 Exit Criteria:**
- System runs in production with HTTPS on a real domain
- All tests pass, >80% coverage
- UI looks polished with animations
- Any developer can clone the repo, follow README, and have it running in <30 minutes

---

## Technical Decisions Log

| Decision | Chosen | Rejected | Reason |
|----------|--------|----------|--------|
| Backend framework | FastAPI | NestJS, Django | Async-native, Python ecosystem for AI |
| ORM | SQLModel | SQLAlchemy alone, Tortoise | Combines Pydantic v2 + SQLAlchemy, less boilerplate |
| Task queue | Redis Streams | Celery, RQ | No extra broker needed, replay/consumer groups |
| Real-time | WebSockets + Redis pub/sub | SSE, polling | Bidirectional, scales across API instances |
| LLM calls | Separate worker process | FastAPI background tasks | Avoids blocking HTTP event loop |
| Canvas | Konva.js | Three.js, D3, CSS | 2D-optimized, React bindings, good perf |
| State | Zustand | Redux, Jotai | Minimal boilerplate, TypeScript-friendly |
| Server state | TanStack Query | SWR, Apollo | Best caching + optimistic updates DX |
| Drag & drop | dnd-kit | react-beautiful-dnd | Maintained, accessible, Kanban support |
| Styling | Tailwind + Shadcn/ui | MUI, Ant Design | Utility-first, fully customizable |

---

---

## Phase 7 — Messaging Platform Integrations

**Goal**: Users can interact with their agent team directly from Telegram, WhatsApp, Discord, and Slack — same orchestrator, same agents, new channels.

### 7.1 Database + Models

- [ ] Create `app/models/messaging.py` — `MessagingChannel`, `Conversation`, `ConversationMessage` SQLModel classes
- [ ] Add `MessagingPlatformEnum`, `MessageDirectionEnum` to `app/models/enums.py`
- [ ] Generate Alembic migration: `alembic revision --autogenerate -m "add_messaging_tables"`
- [ ] Run migration: `alembic upgrade head`

### 7.2 Messaging Module Scaffold

- [ ] Create `app/messaging/` directory with `__init__.py`
- [ ] Create `app/messaging/base.py` — `BasePlatformAdapter` ABC, `InboundMessage` model
- [ ] Create `app/messaging/service.py` — `MessagingService`: `get_or_create_conversation()`, `save_message()`, `update_history()`
- [ ] Create `app/messaging/dispatcher.py` — `MessageDispatcher`: normalize → orchestrator → send reply
- [ ] Create `app/messaging/adapters/__init__.py` — `ADAPTERS` dict, `get_adapter()` factory

### 7.3 Platform Adapters

- [ ] Create `app/messaging/adapters/telegram.py` — `TelegramAdapter`:
  - `verify_signature()`: compare `X-Telegram-Bot-Api-Secret-Token` header
  - `parse_inbound()`: extract `message.text` from Update object
  - `send_message()`: `POST https://api.telegram.org/bot{token}/sendMessage`
- [ ] Create `app/messaging/adapters/whatsapp.py` — `WhatsAppAdapter`:
  - `verify_signature()`: HMAC-SHA256 of raw body with App Secret
  - `parse_inbound()`: extract text from `entry[0].changes[0].value.messages[0]`
  - `send_message()`: `POST https://graph.facebook.com/v19.0/{phone_id}/messages`
- [ ] Create `app/messaging/adapters/discord.py` — `DiscordAdapter`:
  - `verify_signature()`: Ed25519 signature verification (cryptography library)
  - `parse_inbound()`: handle type 0 messages
  - `send_message()`: `POST https://discord.com/api/v10/channels/{id}/messages`
- [ ] Create `app/messaging/adapters/slack.py` — `SlackAdapter`:
  - `verify_signature()`: HMAC-SHA256 with timestamp replay protection (5 min window)
  - `parse_inbound()`: extract from `event.message`
  - `send_message()`: `POST https://slack.com/api/chat.postMessage`

### 7.4 Webhook Router

- [ ] Create `app/messaging/router.py`:
  - `POST /webhooks/telegram/{channel_id}`
  - `GET /webhooks/whatsapp/{channel_id}` (verification challenge)
  - `POST /webhooks/whatsapp/{channel_id}`
  - `POST /webhooks/discord/{channel_id}` (handle PING → return `{"type":1}`)
  - `POST /webhooks/slack/{channel_id}` (handle url_verification challenge)
  - `GET /messaging/channels`
  - `POST /messaging/channels`
  - `PUT /messaging/channels/{id}`
  - `DELETE /messaging/channels/{id}`
  - `GET /messaging/channels/{id}/conversations`
- [ ] Register router in `app/main.py`

### 7.5 Dispatcher Integration

- [ ] Wire `MessageDispatcher` to use `OrchestratorService.handle_chat()`
- [ ] Pass `conversation.history[-10:]` as context to orchestrator
- [ ] Format orchestrator `actions` list as readable text for messaging platforms (emojis + action summaries)
- [ ] Handle errors gracefully — send user-friendly error message back on orchestrator failure

### 7.6 Frontend — Messaging Settings

- [ ] Create `app/settings/messaging/page.tsx` — channel management page:
  - List channels with platform icon, name, status badge, copy-webhook-URL button
  - Create/edit/delete channels
- [ ] Create `components/messaging/ChannelCard.tsx` — platform icon + name + status + webhook URL
- [ ] Create `components/messaging/ChannelFormModal.tsx` — dynamic fields per platform (Telegram/WhatsApp/Discord/Slack)
- [ ] After channel creation: display the webhook URL to configure in the platform dashboard
- [ ] Add "Messaging" link to navigation sidebar

### 7.7 Environment Variables

- [ ] Update `.env.example` with all messaging env var examples:
  - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_SECRET_TOKEN`
  - `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`
  - `DISCORD_BOT_TOKEN`, `DISCORD_APPLICATION_ID`, `DISCORD_PUBLIC_KEY`
  - `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`

### 7.8 Tests

- [ ] `tests/unit/test_telegram_adapter.py` — signature verification, message parsing, send
- [ ] `tests/unit/test_whatsapp_adapter.py` — HMAC verification, challenge response, parse edge cases
- [ ] `tests/unit/test_message_dispatcher.py` — orchestrator called with correct context, reply sent
- [ ] `tests/integration/test_messaging_api.py` — channel CRUD, conversation listing

**Phase 7 Exit Criteria:**
- At least Telegram + WhatsApp fully working end-to-end
- Sending a message on Telegram creates tasks visible in the Kanban board
- Messaging settings page allows full channel management without touching code
- All adapter tests passing

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM provider API outage | Medium | High | Fallback provider in LlmConfig, retry logic |
| Agent stuck in infinite loop | Low | Medium | max_iterations=20 enforced, timeout per tool |
| WebSocket disconnect | Medium | Low | Auto-reconnect in frontend, activity feed degrades gracefully |
| Tool execution security | Medium | High | Command whitelist, path jail, domain whitelist, asyncio timeout |
| DB migration failure | Low | High | Always test migration on staging first, rollback plan |
| Cost overrun (LLM) | Medium | Medium | CostLimitExceeded exception, per-session limits, daily alerts |
