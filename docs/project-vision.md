# Qubot — Visión Completa del Proyecto
> **Documento de contexto permanente** | Versión: 2.0 | Actualizado: 2026-03-16

---

## ¿Qué es Qubot?

Qubot es una **aplicación web de Mission Control para equipos de agentes de IA**, ambientada en una oficina de coworking digital. No es solo un asistente personal — es una plataforma que permite crear, configurar y visualizar un equipo completo de agentes de IA trabajando en conjunto, cada uno con su rol, personalidad, modelo LLM propio, herramientas asignadas y representación visual como personaje de videojuego.

**Inspiración**: OpenClaw, PicoClaw, y el concepto de "personal OS" para agentes de IA, pero llevado a un nivel mucho más visual, gamer e interactivo — con todo configurable desde la UI.

---

## Concepto Central

```
El usuario habla con el Agente Principal (Orquestador)
       ↓
El Orquestador decide qué hacer y a quién delegarlo
       ↓
Sub-agentes ejecutan tareas usando sus herramientas
       ↓
Todo se ve en tiempo real en el Mission Control (Kanban + Coworking visual)
```

Lo que hace a Qubot diferente:
1. **Configuración 100% visual** — wizard de creación de agentes tipo "crear personaje de RPG"
2. **Representación gráfica** — cada agente es un personaje con apariencia basada en su rol
3. **Multi-dominio** — agentes de tecnología, finanzas, RRHH, marketing, legal, etc.
4. **Arquitectura modular** — tools, skills y servicios configurables por UI

---

## 1. Arquitectura del Sistema

### 1.1 Capas

```
┌───────────────────────────────────────────────────────────────┐
│  CAPA 4 — INTERFAZ (Mission Control)                         │
│  • Vista Coworking: personajes en oficina, drag&drop         │
│  • Kanban: tareas en columnas BACKLOG/IN_PROGRESS/DONE       │
│  • Activity Feed: logs en tiempo real via WebSocket          │
│  • Editor visual de agentes (wizard 6 pasos)                 │
│  • Panel de configuración de LLMs, tools y servicios        │
├───────────────────────────────────────────────────────────────┤
│  CAPA 3 — ORQUESTADOR (Core)                                 │
│  • Agente principal que recibe mensajes del usuario          │
│  • Decide: responder directo O crear/asignar tareas          │
│  • Mantiene estado global: colas, logs, estado de agentes    │
│  • Genera JSON de acciones estructuradas                     │
├───────────────────────────────────────────────────────────────┤
│  CAPA 2 — AGENTES                                            │
│  • Entidades con: rol, clase, dominio, personalidad          │
│  • Modelo LLM propio + parámetros (temperature, topP, etc.)  │
│  • Tools asignadas con permisos granulares                   │
│  • Loop: prompt → LLM → tool calls → resultados → loop      │
├───────────────────────────────────────────────────────────────┤
│  CAPA 1 — RECURSOS / HERRAMIENTAS                            │
│  • Adaptadores: web browser, shell, filesystem, HTTP API     │
│  • Scheduler de tareas recurrentes                           │
│  • Los agentes NUNCA hablan directo con la red/SO            │
│  • Permisos por agente: READ_ONLY, READ_WRITE, DANGEROUS     │
└───────────────────────────────────────────────────────────────┘
```

### 1.2 Stack Tecnológico

| Capa | Tecnología | Razón |
|------|-----------|-------|
| **Backend** | Python 3.12 + FastAPI + SQLModel | Async nativo, tipo seguro, ORM integrado |
| **Base de datos** | PostgreSQL 16 + JSONB | Relacional + configs flexibles en JSON |
| **Cache / Eventos** | Redis 7 (Streams) | Estado en tiempo real, pub/sub, colas |
| **Frontend** | Next.js 14 App Router + TypeScript strict | SSR, file-based routing, DX moderno |
| **Estado global** | Zustand | Minimalista, reactivo, sin boilerplate |
| **Estilo** | Tailwind CSS + glassmorphism custom | Utilitario + efectos premium |
| **Auth** | JWT: access_token (localStorage) + refresh_token (HttpOnly cookie) | Seguridad + UX |
| **Realtime** | WebSocket (FastAPI) + Redis pub/sub | Activity feed + estados en vivo |
| **Deploy local** | Docker Compose (6 servicios) | Reproducible, un solo comando |
| **Observabilidad** | structlog + Prometheus + Grafana | Logs estructurados + métricas |
| **Rate limiting** | slowapi + Redis (fallback memory) | Anti-brute force, anti-spam |

---

## 2. Modelo de Datos Completo

### 2.1 `Agent` — Agente

```python
Agent:
  id: UUID
  name: str                          # Nombre visible del agente
  gender: GenderEnum                 # MALE, FEMALE, NON_BINARY
  class_id: UUID → AgentClass        # Clase asignada
  domain: DomainEnum                 # TECH, FINANCE, BUSINESS, HR, MARKETING, LEGAL, OTHER
  role_description: str              # Descripción breve del rol
  personality: JSON                  # gustos, fortalezas, debilidades, estilo de trabajo
  llm_config_id: UUID → LlmConfig    # Modelo LLM asignado
  avatar_config: JSON                # sprite_id, color_primary, color_secondary, icon, badge
  status: StatusEnum                 # IDLE, WORKING, ERROR, OFFLINE
  current_task_id: UUID | null       # FK a tarea en curso
  is_orchestrator: bool              # True solo para el agente principal
  created_at, updated_at: datetime
```

### 2.2 `AgentClass` — Clases de Agente

```python
AgentClass:
  id: UUID
  name: str                          # "Ethical Hacker", "Finance Manager", etc.
  description: str                   # Descripción funcional
  domain: DomainEnum
  is_custom: bool                    # True si la creó el usuario, False si es predefinida
  default_avatar_config: JSON        # Apariencia por defecto para esta clase
```

**Clases predefinidas implementadas:**

| Dominio | Clases |
|---------|--------|
| TECH | Ethical Hacker · Systems Architect · Backend Developer · Frontend Developer · DevOps Engineer · Data Scientist · ML Engineer · Data Analyst · QA Engineer · AI Researcher |
| FINANCE | Finance Manager · Financial Analyst |
| BUSINESS | Product Manager · Operations Manager |
| HR | HR Manager |
| MARKETING | Digital Marketing Specialist |
| LEGAL | Legal Counsel |

**Clases personalizadas**: el usuario puede crear cualquier clase con nombre libre (ej: "Gerente de Finanzas LATAM", "Coach de Productividad"). Se guardan con `is_custom = true`.

### 2.3 `LlmConfig` — Configuración de Modelos

```python
LlmConfig:
  id: UUID
  name: str                          # "GPT-4o Mini", "Claude 3.5 Sonnet", etc.
  provider: LlmProviderEnum          # OPENAI, ANTHROPIC, GOOGLE, GROQ, LOCAL, OTHER
  model_name: str                    # "gpt-4o-mini", "claude-3-5-sonnet-20241022"
  temperature: float                 # 0.0 - 2.0
  top_p: float
  max_tokens: int
  api_key_ref: str                   # Referencia a env var (no guarda la key directo)
  extra_config: JSON                 # endpoint, headers, etc.
```

### 2.4 `Tool` — Herramientas

```python
Tool:
  id: UUID
  name: str
  type: ToolTypeEnum                 # SYSTEM_SHELL, WEB_BROWSER, FILESYSTEM, HTTP_API, SCHEDULER, CUSTOM
  description: str                   # Para que el LLM entienda cuándo usarla
  input_schema: JSON                 # JSON Schema del input
  output_schema: JSON                # JSON Schema del output
  config: JSON                       # base_url, headers, auth, comandos permitidos, etc.

AgentTool (many-to-many):
  agent_id: UUID
  tool_id: UUID
  permissions: PermissionEnum        # READ_ONLY, READ_WRITE, DANGEROUS
```

### 2.5 `Task` — Tareas

```python
Task:
  id: UUID
  title: str
  description: str
  status: TaskStatusEnum             # BACKLOG, IN_PROGRESS, IN_REVIEW, DONE, FAILED
  priority: PriorityEnum             # LOW, MEDIUM, HIGH, CRITICAL
  domain_hint: DomainEnum | null     # Ayuda al orquestador a elegir agente
  created_by: str                    # "user" o "orchestrator"
  assigned_agent_id: UUID | null
  created_at, updated_at, completed_at: datetime

TaskEvent:
  id: UUID
  task_id: UUID
  type: EventTypeEnum                # CREATED, ASSIGNED, STARTED, TOOL_CALL, PROGRESS_UPDATE, COMPLETED, FAILED, COMMENT
  payload: JSON                      # Detalles del evento
  timestamp: datetime
```

### 2.6 Memoria

```python
GlobalMemory:           # Documentos y notas compartidas por todos los agentes
AgentMemory:            # Memoria específica por agente (estilo, preferencias, historial)
TaskMemory:             # Resúmenes y logs por tarea completada
# Estructura preparada para vector DB (pgvector / Weaviate) a futuro
```

---

## 3. Flujo de Orquestación

### 3.1 Recepción de mensaje del usuario

```
Usuario → endpoint /chat → Agente Principal (Orquestador)
```

El orquestador recibe:
- Mensaje del usuario
- Contexto resumido de tareas recientes
- Lista de agentes disponibles (clase, dominio, estado, carga de trabajo)

El LLM del orquestador produce un JSON estructurado:

```json
{
  "response": "Texto inmediato al usuario (si aplica)",
  "actions": [
    {
      "type": "CREATE_TASK",
      "payload": {
        "title": "Analizar balances Q1",
        "description": "...",
        "domain_hint": "FINANCE",
        "preferred_class": "Financial Analyst",
        "priority": "HIGH"
      }
    },
    {
      "type": "ASSIGN_TASK",
      "payload": {
        "task_id": "uuid-existente",
        "agent_id": "uuid-del-agente"
      }
    }
  ]
}
```

### 3.2 Asignación de tareas

El Task Scheduler:
1. Filtra agentes por `domain_hint` y clase preferida
2. Considera carga de trabajo actual (cuántas tareas tiene en progreso)
3. Elige el agente más disponible y adecuado
4. Actualiza `assigned_agent_id` + `status = IN_PROGRESS`
5. Emite evento via WebSocket para actualizar el Kanban en tiempo real

### 3.3 Loop de ejecución del agente

```
1. Construir prompt:
   - Descripción de tarea
   - Memoria relevante del agente
   - Lista de tools disponibles (formato function-calling)
   - Personality del agente

2. Llamar al LLM del agente

3. El LLM responde con:
   - Pensamiento interno (CoT)
   - Tool call a ejecutar (JSON)

4. Backend ejecuta la tool (sandbox)
   - Registra TaskEvent (TOOL_CALL)
   - Emite al Activity Feed via WebSocket

5. Devolver resultado al LLM como siguiente mensaje

6. Repetir desde paso 2 hasta:
   - LLM marca tarea como COMPLETED → status = DONE
   - LLM marca tarea como FAILED → status = FAILED
   - Timeout excedido → FAILED con error
```

---

## 4. Interfaz de Usuario

### 4.1 Vista Coworking ("Deep Space HQ")

Sala de oficina futurista SVG con glassmorphism. Todos los agentes aparecen como personajes en sus escritorios.

**Elementos de la sala:**
- `PremiumFloor` — suelo de mármol negro con gradiente
- `PremiumBackWall` — pared trasera con patrón sutil y separador luminoso
- `PremiumWindows` — ventanas con silueta de ciudad nocturna, estrellas, luna
- `HolographicDisplay` — pantalla holográfica animada con nombre del proyecto (reemplaza la pizarra)
- `PremiumBookshelf` — librería minimalista
- `PremiumServerRack` — rack de servidores con LEDs de actividad animados
- `PremiumPlant` — plantas decorativas SVG
- `PremiumClock` — reloj analógico con hora real del sistema

**Escritorio por agente (`AgentDesk`):**
- Avatar circular con anillo de color según estado
- Anillo pulsante (`animate-ping`) cuando está en WORKING
- Corona para el agente orquestador/lead
- Monitor con líneas de código animadas
- Teclado (grid de teclas SVG)
- Nameplate glassmorphism con nombre, badge de rol y dot de estado
- Drag & drop libre dentro del canvas (posición persiste en localStorage)

**Estados visuales:**
| Estado | Visual |
|--------|--------|
| `WORKING` / `busy` | Verde esmeralda + `animate-ping` en anillo |
| `IDLE` | Pizarra / gris |
| `ERROR` | Rojo + glow de alerta |
| `OFFLINE` | Gris oscuro, sin brillo |

**Temas:** Night (principal) · Day · Sunset — cambiables en tiempo real

### 4.2 Mission Control / Kanban

- Columnas: **BACKLOG** · **IN_PROGRESS** · **IN_REVIEW** · **DONE**
- Tarjetas con: título, avatar del agente asignado, prioridad, dominio
- Drag & drop manual para cambiar columna o agente asignado
- Auto-movimiento cuando el agente cambia el estado de la tarea
- Cada cambio hace PATCH al backend y se refleja en todos los clientes via WebSocket

### 4.3 Wizard de Creación de Agente (6 pasos)

```
Paso 1: DOMINIO
  Selección visual con iconos de dominio
  (TECH, FINANCE, BUSINESS, HR, MARKETING, LEGAL, OTHER)

Paso 2: CLASE
  Lista de AgentClass filtradas por dominio elegido
  + opción "Crear clase personalizada"
    → Formulario: nombre libre, descripción, dominio, config visual

Paso 3: IDENTIDAD
  - Nombre del agente (texto libre)
  - Género (MALE, FEMALE, NON_BINARY)
  - Preview del avatar con el avatar config de la clase elegida

Paso 4: PERSONALIDAD
  - Sliders: detalle ↔ visión global
  - Sliders: conservador ↔ arriesgado con tools
  - Sliders: formal ↔ informal en lenguaje
  - Campo libre de fortalezas, gustos, etc.
  → Se guarda en personality JSON y se inyecta en el system prompt

Paso 5: CONFIG LLM
  - Dropdown de provider (OPENAI, ANTHROPIC, GOOGLE, GROQ, LOCAL)
  - Dropdown de modelo filtrado por provider
  - Sliders: temperature, topP, maxTokens

Paso 6: HERRAMIENTAS
  - Checklist de tools disponibles
  - Permisos por tool (READ_ONLY, READ_WRITE, DANGEROUS)
  - Preview del agente terminado
```

Al finalizar: se crea el `Agent` en la DB y aparece en el canvas del coworking.

### 4.4 Activity Feed (tiempo real)

Panel de logs via WebSocket:
```
10:49:42  ✅ DONE     [Finance Manager]  Completó: "Análisis Q1 balances"
10:48:13  ⚙️ WORKING  [Backend Dev]      Ejecutó tool: HTTP_API POST /users
10:47:01  📋 TASK     [Orchestrator]     Asignó tarea a QA Engineer
10:44:11  👤 USER     [Lead]             Nueva solicitud del usuario
10:43:00  ❌ ERROR    [Hacker]           Tool falló: web_browser timeout
```

### 4.5 Panel de Configuración de Tools

- Listado de todas las tools con: nombre, tipo, agentes que la usan
- Formulario para crear/editar tool:
  - Para `HTTP_API`: base URL, método, headers, auth scheme, schema input/output
  - Para `SYSTEM_SHELL`: lista de comandos permitidos, directorio base, sandbox level
- Asignación de tools a agentes con control de permisos

---

## 5. Sistema de Seguridad

| Medida | Implementación |
|--------|---------------|
| Auth | JWT RS256, access token 1 día, refresh token 7 días (HttpOnly cookie) |
| Sesiones | Tabla `UserSession` con revocación individual o global |
| Passwords | bcrypt (passlib) |
| Rate limiting | slowapi: 5/min en login, 3/min en registro, 100/min en API general |
| CORS | Lista blanca de origins en settings |
| Headers | X-Frame-Options, X-Content-Type-Options, CSP, HSTS, Permissions-Policy |
| API Keys | Referenciadas por nombre de env var, nunca en DB |
| Logs | structlog — nunca loguea passwords ni tokens |

---

## 6. Integraciones Planeadas (Roadmap Futuro)

### 6.1 Canales externos
- **Telegram**: el orquestador recibe mensajes y responde por Telegram
- **Discord**: bot que acepta comandos y reporta resultados
- **Slack**: integración con workspaces empresariales

### 6.2 Automatización
- **n8n**: webhooks bidireccionales para disparar tareas desde workflows de n8n
- **Scheduler**: tareas recurrentes (cron-like) configurables por UI

### 6.3 Memoria semántica
- **pgvector** o **Weaviate** para búsqueda semántica en memoria de agentes
- RAG: los agentes buscan en su memoria histórica al planificar

### 6.4 Marketplace de tools
- Catálogo de integraciones listas: GitHub, Jira, Notion, HubSpot, Slack, etc.
- Import de OpenAPI spec para generar tools automáticamente
- Tools de comunidad (open source)

---

## 7. Rutas y APIs

### Frontend (Next.js)

| Ruta | Componente | Estado |
|------|-----------|--------|
| `/` | Redirect → `/dashboard` | ✅ |
| `/login` | LoginPage | ✅ |
| `/register` | RegisterPage | ✅ |
| `/dashboard` | CoworkingDashboard + OfficeSystem | ✅ |
| `/mission-control` | KanbanBoard | ✅ |
| `/agents` | AgentList | ✅ |
| `/agents/new` | AgentWizard (6 steps) | ✅ |
| `/agents/[id]` | AgentDetail | 🔲 |
| `/tools` | ToolsManager | 🔲 |
| `/settings` | Settings global | 🔲 |
| `/settings/llm` | LLM Config | 🔲 |

### Backend (FastAPI — `/api/v1`)

| Módulo | Endpoints |
|--------|-----------|
| `auth` | POST /login · /register · /logout · /refresh · /me · /api-key |
| `agents` | GET/POST /agents · GET/PATCH/DELETE /agents/{id} |
| `agent-classes` | GET /agent-classes · POST (custom) · GET/PATCH/DELETE /{id} |
| `tasks` | GET/POST /tasks · GET/PATCH/DELETE /{id} · PATCH /{id}/status · GET /kanban/board |
| `tools` | GET/POST /tools · GET/PATCH/DELETE /{id} |
| `llm-configs` | GET/POST /llm-configs · GET/PATCH/DELETE /{id} |
| `memories` | GET/POST /memories |
| `execution` | POST /execute (tool execution) |
| `chat` | POST /chat (orquestador) |
| `websocket` | WS /ws/{client_id} |
| `system` | GET /health · /health/ready · /metrics |

---

## 8. Estructura de Archivos

```
qubot/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/      # auth, agents, tasks, tools, llm_configs, chat, websocket...
│   │   ├── core/               # security, rate_limit, metrics, realtime, exceptions, logging
│   │   ├── models/             # agent, task, user, llm, tool (SQLModel)
│   │   ├── schemas/            # Pydantic schemas para request/response
│   │   ├── services/           # agent_service, task_service (lógica de negocio)
│   │   ├── seeds/              # Datos iniciales: agent_classes, llm_configs
│   │   ├── config.py           # Settings via pydantic-settings
│   │   ├── database.py         # AsyncEngine, AsyncSession
│   │   └── main.py             # FastAPI app factory + middlewares
│   ├── scripts/
│   │   ├── seed_db.py          # Seed inicial de la DB
│   │   └── init_tables.py
│   ├── tests/
│   ├── Dockerfile
│   └── Dockerfile.worker
│
├── frontend/
│   ├── app/                    # Next.js App Router
│   │   ├── dashboard/          # Vista principal (coworking)
│   │   ├── mission-control/    # Kanban
│   │   ├── agents/             # Lista + wizard
│   │   ├── login/
│   │   └── register/
│   ├── components/
│   │   ├── coworking/
│   │   │   ├── OfficeSystem.tsx    # Canvas SVG completo
│   │   │   └── AgentDesk.tsx       # Escritorio individual
│   │   ├── agents/wizard/      # Step1Domain...Step6Tools + AgentWizard
│   │   ├── kanban/             # KanbanBoard + KanbanCard
│   │   └── ui/                 # Componentes reutilizables
│   ├── hooks/                  # useAgents, useTasks, useWebSocket
│   ├── lib/api.ts              # fetchWithAuth + authApi + agentsApi + tasksApi
│   ├── store/auth.store.ts     # Zustand auth state
│   ├── types/index.ts          # TypeScript types completos
│   ├── middleware.ts            # Protección de rutas (lee refresh_token cookie)
│   └── Dockerfile
│
├── nginx/                      # Reverse proxy config
├── monitoring/                 # Prometheus + Grafana
├── k8s/                        # Kubernetes manifests (futuro)
├── docker-compose.yml          # Servicios: db, redis, api, worker, frontend, nginx
├── docker-compose.prod.yml     # Overrides de producción
├── Makefile                    # Comandos de dev: make up, make logs, make seed, etc.
└── docs/
    ├── project-vision.md       ← ESTE ARCHIVO
    ├── design-system-v2.md     # Tokens, componentes, decisiones de diseño premium
    ├── architecture.md         # Diagramas detallados
    ├── api-specification.md    # OpenAPI / Swagger docs
    ├── database-schema.md      # ERD + tablas
    ├── deployment.md           # Guía de deploy a producción
    └── ...
```

---

## 9. Estado Actual de Implementación (2026-03-16)

### ✅ Completado

- **Backend completo**: todos los endpoints CRUD, auth con JWT + sessions, WebSocket, rate limiting, structlog, métricas Prometheus, CSP headers, seeds de datos
- **Frontend completo**: dashboard coworking, kanban, wizard de agentes (6 pasos), auth flow (login/register/logout/refresh), protección de rutas via middleware
- **Diseño premium v2**: glassmorphism "Deep Space HQ", OfficeSystem con 8 sub-componentes SVG, AgentDesk 3D, tres temas (night/day/sunset), animaciones CSS/Tailwind
- **Docker Compose**: 6 servicios corriendo (db, redis, api, worker, frontend, nginx)
- **Auth segura**: cookie HttpOnly para refresh_token, access_token en localStorage, no cookies JS-accesibles vulnerables a XSS

### 🔲 Próximas Fases

| Fase | Descripción | Prioridad |
|------|-------------|-----------|
| 6 | Loop de ejecución real: orquestador LLM + tool execution + sub-agentes | Alta |
| 7 | Integración Telegram (gateway multi-canal) | Media |
| 7 | n8n webhooks bidireccionales | Media |
| 8 | Memoria vectorial con pgvector + RAG por agente | Media |
| 9 | Marketplace de tools (OpenAPI import, catálogo) | Baja |
| 9 | Niveles de XP por agente, animaciones de "loot", efectos gamer | Baja |
| 10 | App móvil React Native / Expo | Baja |

---

## 10. Comandos de Desarrollo

```bash
# Levantar todo (local)
docker-compose up -d

# Reconstruir un servicio
docker-compose build --no-cache api && docker-compose up -d api

# Ver logs
docker-compose logs -f api
docker-compose logs -f frontend

# Acceder a la DB
docker exec -it qubot-db psql -U qubot -d qubot_db

# URLs locales
# Frontend:     http://localhost:3000
# Backend API:  http://localhost:8000
# API docs:     http://localhost:8000/docs  (solo con DEBUG=true)
# Health:       http://localhost:8000/api/v1/health
```

---

*Este documento es el contexto permanente del proyecto Qubot. Toda sesión de desarrollo debe partir de aquí para entender el estado actual y las próximas prioridades.*
