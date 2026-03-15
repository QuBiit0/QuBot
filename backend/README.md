# Qubot Backend

Multi-agent AI platform backend built with FastAPI, SQLModel, and PostgreSQL.

## Features

- **Multi-Agent Orchestration**: Coordinate multiple AI agents for complex tasks
- **LLM Integration**: Support for OpenAI, Anthropic, Google, Groq, and Ollama
- **Tool System**: HTTP API, Shell, Browser, Filesystem, and Scheduler tools
- **Memory System**: Global, agent-specific, and task memory with context injection
- **Real-time Communication**: WebSocket with Redis pub/sub
- **Authentication**: JWT with role-based access control
- **Scalable Architecture**: Kubernetes-ready with HPA and worker queues

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Seed database
python -c "from scripts.seed_db import seed; seed()"

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start worker
python -m app.worker
```

### Docker Compose

```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head
```

### Kubernetes Deployment

```bash
# Create namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy application
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n qubot
```

## API Endpoints

### System
- `GET /api/v1/health` - Health check
- `GET /api/v1/metrics` - System metrics
- `GET /api/v1/info` - System info

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Agents
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents/{id}` - Get agent details
- `PATCH /api/v1/agents/{id}/status` - Update status

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `POST /api/v1/tasks/{id}/execute` - Execute task
- `POST /api/v1/tasks/{id}/submit` - Submit to queue
- `GET /api/v1/tasks/kanban/board` - Kanban board

### Orchestrator
- `POST /api/v1/orchestrator/process` - Process complex task

### LLM
- `GET /api/v1/llm-configs` - List LLM configurations
- `POST /api/v1/llm-configs/{id}/chat` - Chat completion

### Tools
- `GET /api/v1/tools/available` - List available tools
- `POST /api/v1/tools/execute` - Execute tool
- `POST /api/v1/tools/execute-with-llm` - Execute with LLM

## WebSocket

Connect to `ws://localhost:8000/ws` for real-time updates.

Events:
- `task.created`, `task.completed`, `task.failed`
- `agent.status_changed`
- `tool.executed`
- `activity.log`
- `metrics.updated`

## Architecture

```
┌─────────────────┐
│   API (FastAPI) │
└────────┬────────┘
         │
    ┌────┴────┬────────┐
    │         │        │
Services  Providers  Tools
    │         │        │
┌───┴───┐ ┌───┴───┐ ┌──┴────┐
│Agent  │ │OpenAI │ │HTTP   │
│Task   │ │Claude │ │Shell  │
│Memory │ │Groq   │ │Browser│
└───┬───┘ └───────┘ └───────┘
    │
┌───┴───────────────┐
│ PostgreSQL + Redis │
└────────────────────┘
```

## Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `false` |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `ALLOWED_ORIGINS` | CORS origins | `*` |

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── endpoints/      # API routes
│   ├── core/
│   │   ├── providers/      # LLM providers
│   │   ├── tools/          # Tool implementations
│   │   ├── security.py     # Auth & JWT
│   │   └── cache.py        # Caching
│   ├── models/             # SQLModel models
│   ├── services/           # Business logic
│   ├── database.py         # DB connection
│   ├── config.py           # Settings
│   └── main.py             # FastAPI app
├── tests/                  # Test suite
├── alembic/                # Migrations
└── requirements.txt        # Dependencies
```

## Production Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up Redis
- [ ] Configure SSL/TLS
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up backups
- [ ] Configure rate limiting
- [ ] Review security settings

## License

MIT License - See LICENSE file for details
