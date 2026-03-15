# Qubot - AI Office Platform

Qubot es una plataforma visual de agentes de IA multi-modelo que funciona como una oficina de coworking para agentes autónomos de IA.

## 🚀 Características

- **🤖 Agentes de IA Multi-Modelo**: Soporte para OpenAI, Anthropic, Google, Groq y modelos locales
- **🎨 Oficina Virtual Visual**: Interfaz tipo coworking con avatares y posiciones en canvas
- **📋 Sistema de Tareas Kanban**: Gestión visual de tareas con drag & drop
- **⚡ Tiempo Real**: WebSocket para actualizaciones en vivo
- **🔒 Autenticación Segura**: JWT con refresh tokens y API keys
- **📊 Métricas Prometheus**: Monitoreo completo con métricas exportables
- **🧪 Testing**: Tests unitarios e integración con pytest

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │   Canvas     │  │    Chat      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket / HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Agents    │  │    Tasks     │  │     LLM      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Auth      │  │    Tools     │  │  WebSocket   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │PostgreSQL│       │  Redis  │       │Prometheus│
   └─────────┘       └─────────┘       └─────────┘
```

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** - Framework web de alto rendimiento
- **SQLModel** + **SQLAlchemy** - ORM y modelos
- **PostgreSQL** - Base de datos principal
- **Redis** - Cache y pub/sub
- **Celery** (Worker) - Procesamiento en background
- **Prometheus Client** - Métricas

### Frontend
- **Next.js 14** - Framework React
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Estilos utilitarios
- **Zustand** - Gestión de estado
- **Framer Motion** - Animaciones
- **@dnd-kit** - Drag & drop

## 🚀 Quick Start

### Requisitos
- Docker Desktop
- Git

### 1. Clonar y Configurar

```bash
git clone <repository-url>
cd qubot

# Crear archivo de entorno
cp .env.example .env
```

### 2. Iniciar con Docker

```bash
# Construir e iniciar todos los servicios
docker-compose -f docker-compose.local.yml up --build

# O usar el script de conveniencia
./scripts/deploy-local.sh
```

### 3. Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Métricas**: http://localhost:8000/api/v1/metrics

## 📝 Variables de Entorno

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://qubot:qubot_pass@db:5432/qubot_db

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
DEBUG=true

# LLM Providers (opcional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
cd backend
pytest

# Ejecutar tests específicos
pytest tests/test_api.py -v
pytest tests/test_auth.py -v

# Con cobertura
pytest --cov=app --cov-report=html
```

## 📊 Métricas

El sistema expone métricas Prometheus en `/api/v1/metrics`:

- **http_requests_total** - Contador de requests HTTP
- **http_request_duration_seconds** - Histograma de latencia
- **qubot_active_agents** - Agentes activos por estado
- **qubot_tasks_total** - Tareas procesadas
- **qubot_llm_calls_total** - Llamadas a LLM
- **qubot_llm_cost_dollars** - Costo acumulado

### Importar en Grafana

```yaml
scrape_configs:
  - job_name: 'qubot'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/metrics'
```

## 🔧 Comandos Útiles

```bash
# Ver logs
docker-compose -f docker-compose.local.yml logs -f

# Reconstruir servicio específico
docker-compose -f docker-compose.local.yml up --build api

# Ejecutar migraciones manualmente
docker exec qubot-api alembic upgrade head

# Backup de base de datos
docker exec qubot-db pg_dump -U qubot qubot_db > backup.sql

# Shell en contenedor
docker exec -it qubot-api bash
```

## 📚 Documentación

- [API Documentation](http://localhost:8000/docs) - Swagger UI
- [DEPLOY.md](DEPLOY.md) - Guía de despliegue en producción
- [DEPLOY_WINDOWS.md](DEPLOY_WINDOWS.md) - Guía para Windows

## 🐛 Troubleshooting

### Error: "useTaskStore is not a function"
**Solución**: Reiniciar los contenedores:
```bash
docker-compose -f docker-compose.local.yml restart
```

### Error: Puerto 3000 en uso
**Solución**: Matar proceso ocupando el puerto:
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Error: PostgreSQL connection failed
**Solución**: Verificar que el contenedor de DB esté healthy:
```bash
docker ps
# Si no está healthy, reiniciar:
docker-compose -f docker-compose.local.yml restart db
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/nueva-feature`)
3. Commit cambios (`git commit -am 'Agregar nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Crear Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

---

Desarrollado con ❤️ usando FastAPI, Next.js y mucho café.
