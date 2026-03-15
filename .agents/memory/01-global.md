# 🧠 Project Identity & Core Goals
> **Update Frequency:** Start of project & Major Pivots.

## 🎯 Mission

**Qubot** es una plataforma multi-agente de IA auto-hospedada que funciona como un "Mission Control" para equipos de agentes de IA. Permite a los usuarios interactuar con un equipo de agentes especializados a través de una interfaz de chat o aplicaciones de mensajería externas, donde un agente orquestador delega el trabajo a sub-agentes especializados.

## 📦 Core Value Proposition

1. **Gamified Coworking Office UI**: Los agentes aparecen como personajes de videojuego en escritorios, con estados visuales (trabajando, idle, error, offline) - diferenciador visual clave.

2. **100% Visual Configuration**: Crear agentes, asignar LLMs, configurar tools, todo sin código - democratiza el acceso a equipos de IA.

3. **Multi-Provider LLM Support**: Configurable por agente (OpenAI, Anthropic, Google, Groq, Ollama, OpenRouter, DeepSeek, Kimi, MiniMax, Zhipu, custom) - agnóstico de proveedor.

4. **Event-Driven Real-Time Updates**: WebSocket + Redis pub/sub para Kanban en vivo, activity feed, estado de agentes - escalable horizontalmente.

5. **Messaging Platform Integrations**: Interactuar con el equipo de agentes vía Telegram, WhatsApp, Discord y Slack - mismo orquestador, nuevos canales.

## 👥 Key Stakeholders / Users

- **Primary**: Equipos técnicos y de negocio que quieren automatizar tareas complejas con múltiples agentes especializados
- **Secondary**: 
  - Desarrolladores que necesitan agents para coding tasks
  - Managers que quieren oversight visual de operaciones de IA
  - Usuarios finales que interactúan vía apps de mensajería

## 🌟 Definition of Success

1. ✅ Usuario puede crear un agente con wizard visual en < 2 minutos
2. ✅ Orquestador puede recibir mensaje, crear tareas y asignarlas a agentes apropiados
3. ✅ Agentes ejecutan tareas usando tools reales (HTTP, shell, browser) con LLM real
4. ✅ Vista coworking muestra agentes animados según estado real del backend
5. ✅ Kanban board actualiza en tiempo real con drag & drop
6. ✅ Soporta al menos 3 providers LLM diferentes
7. ✅ Cost tracking muestra gasto real por agente/tarea
8. ✅ System runs in production with HTTPS on real domain

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│  EXTERNAL WORLD                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Telegram │  │WhatsApp  │  │ Discord  │  │  Slack   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       └─────────────┴─────────────┴──────────────┘              │
│                         │ webhook POST                          │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  qubot-frontend  (Next.js 14, port 3000)                     ││
│  │  • Coworking canvas (Konva.js)                               ││
│  │  • Kanban board (dnd-kit)                                    ││
│  │  • Agent creation wizard                                     ││
│  │  • Activity feed (WebSocket)                                 ││
│  └──────────────────────────────┬───────────────────────────────┘│
│                                 │ HTTP REST + WebSocket          │
│  ┌──────────────────────────────▼──────────────────────────────┐│
│  │  qubot-api  (FastAPI Python 3.12, port 8000)                 ││
│  │  • REST API (CRUD)                                           ││
│  │  • WebSocket hub                                             ││
│  │  • Orchestrator endpoint (/chat)                             ││
│  │  • Messaging ingress (webhooks)                              ││
│  └──────┬─────────────────────────────┬─────────────────────────┘│
│         │ SQL (asyncpg)                │ Redis pub/sub            │
│  ┌──────▼──────────┐      ┌───────────▼─────────────────────┐   │
│  │   qubot-db      │      │  qubot-redis  (Redis 7)         │   │
│  │  (PostgreSQL 16)│      │  • Task queues (Streams)        │   │
│  │                 │      │  • WS event bus (pub/sub)       │   │
│  └─────────────────┘      └───────────┬─────────────────────┘   │
│                                       │ Redis Streams           │
│  ┌────────────────────────────────────▼─────────────────────┐   │
│  │  qubot-worker  (Python asyncio)                           │   │
│  │  • Task execution loop (LLM → tool calls → repeat)       │   │
│  │  • Executes tools (HTTP, shell, browser, filesystem)     │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 📚 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.115+ |
| Python | 3.12+ |
| ORM | SQLModel + SQLAlchemy 2.0+ |
| Database | PostgreSQL 16 |
| Cache/Queues | Redis 7 (Streams + Pub/Sub) |
| Frontend | Next.js 14 (App Router) |
| UI | TailwindCSS + Shadcn/ui |
| Canvas | Konva.js 9+ |
| State | Zustand + TanStack Query |
| Animations | Framer Motion |
| Drag & Drop | dnd-kit |
| LLM Providers | OpenAI, Anthropic, Google, Groq, Ollama, OpenRouter, DeepSeek, Kimi, MiniMax, Zhipu |

## 🎨 Design Principles

1. **Stateless agents**: No in-memory state; all persistence goes to PostgreSQL/Redis
2. **Tool-first reasoning**: LLM decides, tools execute; agents never run code directly
3. **Observable execution**: Every LLM call, tool invocation, task state change is logged
4. **Event-driven UI**: Frontend reacts to server events, never polls
5. **Separation of layers**: Routers → Services → Repositories; no business logic in HTTP handlers

## 🔐 Security Principles

- API keys stored as env var references, never values in DB
- Tool execution: command whitelist, path traversal protection, domain whitelist
- All tool calls: `asyncio.wait_for(..., timeout=60.0)` hard limit
- Tools with `is_dangerous=True` require `PermissionEnum.DANGEROUS` assignment
