# Stack Tecnológico - LMAgent

> **Tipo**: `rule` | **Versión**: 3.0.0 | **Actualización**: 2026-02

## 📌 Quick Reference

| Capa | Tecnología Principal |
|------|----------------------|
| **Backend** | Python 3.11+ (FastAPI) o TypeScript (NestJS) |
| **Database** | PostgreSQL 15+ (principal) + Redis 7+ (cache/colas) |
| **ORM** | SQLModel (Python) o Prisma (TypeScript) |
| **Validation** | Pydantic v2 |
| **LLM** | GPT-4o (complejo) / Gemini Flash (rápido) / Claude Haiku (volumen) |
| **AI Frameworks** | LangGraph (agentes) / LangChain (chains) |
| **Automation** | n8n |
| **Frontend** | React / Next.js |
| **Mobile** | React Native / Expo |
| **Deploy** | Docker + Dokploy |

### 👥 Roles que usan esta regla
`backend-engineer`, `frontend-engineer`, `devops-engineer`, `architect`

---

Este documento define el stack tecnológico base y las buenas prácticas para proyectos que usan LMAgent.

> ⚠️ **FLEXIBILIDAD TECNOLÓGICA (NUEVO ESTÁNDAR)**: Todas las tecnologías, librerías y versiones explícitas (ej. Python 3.14, FastAPI, NestJS) listadas en este documento son **ejemplos de referencia recomendados**. Tienes total libertad y la responsabilidad de proponer, evaluar y utilizar las mejores versiones estables o alternativas modernas disponibles en la actualidad si consideras que son superiores para el proyecto.

## Stack Principal

### Lenguajes
| Lenguaje | Versión | Uso |
|----------|---------|-----|
| Python | 3.14+ | Backends, agentes IA, scripts |
| TypeScript | 5.9+ | Backends Node, frontends |
| JavaScript | ES2026+ | Scripts, n8n custom nodes |

### Frameworks Backend

#### Python (Preferido para APIs y Agentes)
```
FastAPI (0.128+) - Framework web async
SQLModel       - ORM + validación (combina SQLAlchemy + Pydantic)
Pydantic       - Validación de datos
Pydantic-Settings - Configuración via env vars
Uvicorn        - Servidor ASGI
```

#### NodeJS/TypeScript (Cuando sea necesario)
```
NestJS (v11+)  - Framework estructurado (preferido)
Express        - Framework minimalista
Prisma         - ORM para TypeScript
```

### Base de Datos
| Componente | Tecnología | Uso |
|------------|------------|-----|
| Principal | PostgreSQL 17+ | Datos relacionales |
| Cache | Redis 7.4+ | Cache, sesiones, colas |
| Colas | Redis Streams | Mensajería async |
| Búsqueda | PostgreSQL FTS | Búsqueda de texto |

### Infraestructura
| Componente | Tecnología | Uso |
|------------|------------|-----|
| Containers | Docker | Empaquetado |
| Orquestación | Docker Compose | Desarrollo local |
| Deployment | Dokploy | Deploy a producción |
| CI/CD | GitHub Actions | Automatización |

### Automatización e IA
| Componente | Tecnología | Uso |
|------------|------------|-----|
| Orquestación | n8n | Workflows visuales |
| LLM Primary | OpenAI GPT-4o | Tareas complejas |
| LLM Fast | Gemini Flash | Tareas rápidas |
| LLM Cost-effective | Claude Haiku | Alto volumen |
| Agent Framework | LangGraph | Agentes stateful, grafos |
| Chain Framework | LangChain | Chains, RAG, embeddings |
| MCP | Model Context Protocol | Tool-use, integración de herramientas |

### Frontend & Mobile
| Componente | Tecnología | Uso |
|------------|------------|-----|
| Web Framework | React / Next.js | Interfaces web |
| Mobile | React Native / Expo | Apps iOS y Android |
| State | Zustand / Redux Toolkit | Estado global |
| Styling | TailwindCSS / CSS Modules | Estilos |

---

## Estructura de Proyecto

### Monorepo Multi-servicio
```
proyecto/
├── .lmagent/              # Framework LMAgent
├── backend-python/        # API principal (FastAPI)
├── backend-node/          # Servicios Node (opcional)
├── agents/                # Agentes de IA
├── automations/           # Workflows n8n
├── infra/                 # Docker, configs
├── docs/                  # Documentación
└── .github/               # CI/CD
```

### Estructura Backend Python
```
backend-python/
├── app/
│   ├── __init__.py
│   ├── main.py           # Entry point FastAPI
│   ├── config.py         # Configuración
│   ├── routers/          # Endpoints (capa presentación)
│   ├── services/         # Lógica de negocio
│   ├── repositories/     # Acceso a datos
│   ├── models/           # Modelos SQLModel
│   ├── schemas/          # Schemas Pydantic
│   └── core/             # Utilidades compartidas
├── tests/
├── Dockerfile
└── requirements.txt
```

---

## Patrones de Arquitectura

### Capas de la Aplicación
```
┌─────────────────────────────────────┐
│           Routers (API)             │  ← HTTP Request/Response
├─────────────────────────────────────┤
│           Services                  │  ← Lógica de negocio
├─────────────────────────────────────┤
│         Repositories                │  ← Acceso a datos
├─────────────────────────────────────┤
│         Models/Schemas              │  ← Estructuras de datos
└─────────────────────────────────────┘
```

### Principios
1. **Routers**: Solo manejan HTTP, sin lógica de negocio
2. **Services**: Toda la lógica de negocio, sin acceso directo a DB
3. **Repositories**: Acceso a datos, queries, transacciones
4. **Models**: Representan entidades de la base de datos
5. **Schemas**: Validación de input/output de API

---

## Configuración

### Variables de Entorno (obligatorio)
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # API Keys (opcional)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    
    # n8n
    N8N_WEBHOOK_URL: str = ""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### .env.example
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your-super-secret-key-minimum-32-characters

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# n8n
N8N_WEBHOOK_URL=https://n8n.yourserver.com/webhook

# Environment
ENVIRONMENT=development
DEBUG=true
```

---

## Buenas Prácticas

### Obligatorias ✅
- [ ] Configuración via variables de entorno (nunca hardcode)
- [ ] Type hints en todas las funciones
- [ ] Docstrings en funciones públicas
- [ ] Tests para lógica de negocio (>80% coverage)
- [ ] Logging estructurado (JSON en producción)
- [ ] Manejo de errores con excepciones tipadas
- [ ] Validación de input con Pydantic
- [ ] Commits pequeños y descriptivos

### Prohibidas ❌
- [ ] Credenciales en código
- [ ] `print()` en lugar de logging
- [ ] `import *`
- [ ] Lógica de negocio en routers
- [ ] SQL sin parametrizar
- [ ] Commits sin tests
- [ ] PRs gigantes sin dividir

### Recomendadas 💡
- [ ] Usar async/await para I/O
- [ ] Implementar health checks
- [ ] Documentar APIs con OpenAPI
- [ ] Usar dependency injection
- [ ] Implementar rate limiting
- [ ] Agregar métricas de observabilidad

---

## Dependencias

### Python - requirements.txt base
```
# Framework
fastapi>=0.128.0
uvicorn[standard]>=0.34.0

# Database
sqlmodel>=0.0.24
asyncpg>=0.30.0
sqlalchemy[asyncio]>=2.0.36

# Validation
pydantic>=2.10.0
pydantic-settings>=2.7.0

# Redis
redis>=5.2.0

# HTTP Client
httpx>=0.28.0

# Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Logging
structlog>=24.4.0

# Dev
pytest>=9.0.0
pytest-asyncio>=0.25.0
pytest-cov>=6.0.0
ruff>=0.9.0

```

### Node - package.json base
```json
{
  "dependencies": {
    "@nestjs/common": "^11.0.0",
    "@nestjs/core": "^11.0.0",
    "@nestjs/platform-express": "^11.0.0",
    "@prisma/client": "^6.0.0",
    "ioredis": "^5.4.0",
    "class-validator": "^0.14.1",
    "class-transformer": "^0.5.1"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.7.0",
    "jest": "^29.7.0",
    "eslint": "^9.0.0",
    "prettier": "^3.4.0"
  }
}
```

---

## Docker

### Dockerfile Python (multi-stage)
```dockerfile
# Build stage
FROM python:3.14-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.14-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY ./app ./app

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: "3.6.0"

services:
  backend:
    build: ./backend-python
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [n8n Documentation](https://docs.n8n.io/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

---

## ✅ Checklist de Validación (Nuevo Proyecto)

### Setup Inicial
- [ ] Estructura de directorios según patrón definido
- [ ] `.env.example` con todas las variables documentadas
- [ ] `docker-compose.yml` con PostgreSQL + Redis
- [ ] Config via pydantic-settings (no hardcode)

### Código
- [ ] Type hints en todas las funciones
- [ ] Capas separadas: Routers → Services → Repositories
- [ ] Sin credenciales en código
- [ ] Logging con structlog (no print)

### Calidad
- [ ] Tests con pytest, coverage > 80%
- [ ] Linting con ruff pasando
- [ ] CI/CD con GitHub Actions configurado
