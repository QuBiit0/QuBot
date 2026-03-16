# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-03-15

### Added
- FastAPI backend with 14 REST API routers
- PostgreSQL 16 database with 14 SQLModel tables and Alembic migrations
- Redis 7 integration for caching, task queues (Streams), and WebSocket pub/sub
- 5 LLM providers: OpenAI, Anthropic, Google, Groq, Ollama
- 6 tool implementations: HTTP, Shell, Browser, Filesystem, Scheduler
- Multi-agent orchestration with intelligent task assignment
- Background worker with Redis Streams consumer groups
- WebSocket real-time event system
- JWT authentication with refresh tokens
- Rate limiting and security middleware
- Next.js 15 frontend with Tailwind CSS and Shadcn/ui
- Kanban board with drag-and-drop (dnd-kit)
- Coworking office canvas (Konva.js)
- Agent creation wizard (6-step form)
- Zustand state management with TanStack Query
- Docker Compose orchestration (7 services)
- Kubernetes manifests
- Nginx reverse proxy configuration
- Prometheus metrics and Grafana dashboards
- Comprehensive documentation (22 docs)
