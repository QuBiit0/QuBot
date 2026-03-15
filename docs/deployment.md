# Qubot — Deployment Guide

> **Covers**: Docker setup, docker-compose (dev + prod), Nginx, SSL, VPS deployment, Dokploy alternative

---

## 1. Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Docker | 24+ | Engine + CLI |
| Docker Compose | 2.20+ | Usually bundled with Docker Desktop |
| Git | 2.40+ | For cloning |
| Domain | — | Required for SSL in production |

---

## 2. Repository Layout

```
qubot/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── Dockerfile
│   └── ...
├── nginx/
│   ├── nginx.conf           # HTTP (dev/staging)
│   └── nginx.prod.conf      # HTTPS (production)
├── docker-compose.yml       # Development
├── docker-compose.prod.yml  # Production overrides
├── .env.example
└── .gitignore
```

---

## 3. Environment Variables

### `.env.example` — copy to `.env` and fill in values

```bash
# ── Database ──────────────────────────────────────────────────────
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=qubot
POSTGRES_PASSWORD=changeme_strong_password_here
POSTGRES_DB=qubot

# Full async DSN (auto-assembled in config.py, or set explicitly)
# DATABASE_URL=postgresql+asyncpg://qubot:password@postgres:5432/qubot

# ── Redis ─────────────────────────────────────────────────────────
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
# REDIS_URL=redis://redis:6379/0

# ── Security ──────────────────────────────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=replace_with_minimum_32_char_random_string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ── LLM API Keys ──────────────────────────────────────────────────
# These names are referenced by LlmConfig.api_key_ref in the DB.
# Add any keys you plan to use; unused ones can be left empty.
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...

# Ollama (local) — leave empty if not using
OLLAMA_BASE_URL=http://host.docker.internal:11434

# ── Application ───────────────────────────────────────────────────
APP_ENV=production        # development | staging | production
DEBUG=false
LOG_LEVEL=INFO

# Allowed CORS origins — JSON array
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# Worker: max parallel task executions
WORKER_CONCURRENCY=4

# ── Frontend (build-time, Next.js) ────────────────────────────────
NEXT_PUBLIC_API_URL=https://yourdomain.com
NEXT_PUBLIC_WS_URL=wss://yourdomain.com
```

### `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional
import json


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "qubot"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "qubot"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # App
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    WORKER_CONCURRENCY: int = 4

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

## 4. Docker Images

### `backend/Dockerfile`

```dockerfile
# ── Build stage ───────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --user -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────
FROM python:3.12-slim

# Non-root user for security
RUN addgroup --system app && adduser --system --group app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source
COPY --chown=app:app ./app ./app
COPY --chown=app:app alembic.ini .
COPY --chown=app:app alembic/ ./alembic/

USER app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Health check (curl not available in slim — use python)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/system/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### `backend/requirements.txt`

```
# Framework
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9

# Database
sqlmodel==0.0.21
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.3

# Validation
pydantic==2.9.2
pydantic-settings==2.5.2

# Redis
redis[hiredis]==5.1.1

# HTTP
httpx==0.27.2

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# LLM Providers
openai==1.51.0
anthropic==0.36.0
google-generativeai==0.8.3
groq==0.11.0

# Web scraping (for WebBrowserTool)
beautifulsoup4==4.12.3
lxml==5.3.0

# Utilities
tenacity==9.0.0
structlog==24.4.0

# Dev only (remove for production image if desired)
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2   # test client
```

### `frontend/Dockerfile`

```dockerfile
# ── Dependencies stage ────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

# ── Build stage ───────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time env vars must be set at build time for Next.js
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

RUN npm run build

# ── Runtime stage ─────────────────────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system nextjs && adduser --system --group nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000

HEALTHCHECK --interval=30s --timeout=10s CMD \
  wget -qO- http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
```

> **Next.js standalone mode** — add to `next.config.js`:
> ```js
> module.exports = { output: 'standalone' }
> ```

---

## 5. Development Docker Compose

### `docker-compose.yml`

```yaml
version: "3.9"

services:

  # ── PostgreSQL ──────────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: qubot_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-qubot}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devpassword}
      POSTGRES_DB: ${POSTGRES_DB:-qubot}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"   # Expose for local DB tools (pgAdmin, DBeaver)
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-qubot}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Redis ───────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: qubot_redis
    restart: unless-stopped
    command: redis-server --save 60 1 --loglevel warning
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"   # Expose for local inspection (redis-cli)
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Backend API ─────────────────────────────────────────────────
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: qubot_api
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    env_file: .env
    environment:
      POSTGRES_HOST: postgres
      REDIS_HOST: redis
    volumes:
      - ./backend/app:/app/app   # Hot reload in development
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ── Worker Process ──────────────────────────────────────────────
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: qubot_worker
    restart: unless-stopped
    command: python -m app.worker
    env_file: .env
    environment:
      POSTGRES_HOST: postgres
      REDIS_HOST: redis
    volumes:
      - ./backend/app:/app/app   # Hot reload in development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      api:
        condition: service_started

  # ── Frontend ────────────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000
        NEXT_PUBLIC_WS_URL: ws://localhost:8000
    container_name: qubot_frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: qubot_network
```

---

## 6. Production Docker Compose

### `docker-compose.prod.yml` (overrides)

```yaml
version: "3.9"

services:

  postgres:
    ports: []    # Remove external port exposure in prod
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Must be set; no default in prod

  redis:
    ports: []    # Remove external port exposure

  api:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    volumes: []   # No hot reload in production
    restart: always
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G

  worker:
    volumes: []
    restart: always
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G

  frontend:
    volumes: []
    restart: always

  nginx:
    image: nginx:1.25-alpine
    container_name: qubot_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot:ro
    depends_on:
      - api
      - frontend
```

**Deploy with both files:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 7. Nginx Configuration

### `nginx/nginx.conf` — Development (HTTP only)

```nginx
upstream qubot_api {
    server api:8000;
}

upstream qubot_frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name localhost;

    client_max_body_size 50M;

    # API
    location /api/ {
        proxy_pass http://qubot_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws {
        proxy_pass http://qubot_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Frontend (everything else)
    location / {
        proxy_pass http://qubot_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### `nginx/nginx.prod.conf` — Production (HTTPS)

```nginx
upstream qubot_api {
    server api:8000;
    keepalive 32;
}

upstream qubot_frontend {
    server frontend:3000;
    keepalive 16;
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Certbot validation
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    client_max_body_size 50M;

    # Gzip
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # API
    location /api/ {
        proxy_pass http://qubot_api;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://qubot_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Static assets — direct from Next.js
    location /_next/static/ {
        proxy_pass http://qubot_frontend;
        proxy_cache_valid 200 365d;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # Frontend
    location / {
        proxy_pass http://qubot_frontend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 8. VPS Deployment — Step-by-Step

### 8.1 Server Setup (Ubuntu 22.04 LTS)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Verify
docker --version
docker compose version
```

### 8.2 Clone and Configure

```bash
# 1. Clone repository
git clone https://github.com/youruser/qubot.git
cd qubot

# 2. Create environment file
cp .env.example .env
nano .env   # Fill in all values (passwords, JWT secret, API keys)

# 3. Verify .env is not in git
grep ".env" .gitignore   # Should show: .env
```

### 8.3 SSL Certificate (Let's Encrypt)

```bash
# 1. Install certbot
sudo apt install certbot -y

# 2. Open ports (if using UFW)
sudo ufw allow 80
sudo ufw allow 443

# 3. Obtain certificate (standalone mode, before nginx starts)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com \
  --email admin@yourdomain.com --agree-tos --no-eff-email

# Certificates are saved to: /etc/letsencrypt/live/yourdomain.com/

# 4. Update nginx.prod.conf with your domain name
sed -i 's/yourdomain.com/ACTUAL_DOMAIN/g' nginx/nginx.prod.conf
```

### 8.4 First Deployment

```bash
# 1. Build and start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 2. Wait for postgres to be healthy
docker compose ps

# 3. Run database migrations
docker compose exec api alembic upgrade head

# 4. Seed predefined agent classes (17 built-in classes)
docker compose exec api python -m app.seeds.agent_classes

# 5. Create initial admin user
docker compose exec api python -m app.seeds.admin_user

# 6. Health check
curl https://yourdomain.com/api/v1/system/health

# Expected:
# {"status":"healthy","postgres":"connected","redis":"connected"}
```

### 8.5 Verify All Services

```bash
# Service status
docker compose ps

# API logs
docker compose logs api --tail=50

# Worker logs
docker compose logs worker --tail=50

# Follow all logs
docker compose logs -f
```

### 8.6 SSL Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal + nginx reload
sudo crontab -e

# Add this line:
0 3 * * * certbot renew --quiet && docker exec qubot_nginx nginx -s reload
```

---

## 9. Updates and Maintenance

### Deploying Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart (zero-downtime for nginx/frontend)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Run any new migrations
docker compose exec api alembic upgrade head

# Force restart specific service if needed
docker compose restart api
docker compose restart worker
```

### Database Backup

```bash
# Backup
docker compose exec postgres pg_dump -U qubot qubot > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
docker compose exec -T postgres psql -U qubot qubot < backup_20240101_120000.sql
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service, last 100 lines
docker compose logs api --tail=100 -f

# Filter for errors
docker compose logs api 2>&1 | grep -i error
```

### Scaling Workers

```bash
# Run 3 worker instances for more parallel task processing
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  up -d --scale worker=3
```

---

## 10. Alternative: Dokploy Deployment

[Dokploy](https://dokploy.com) provides a Heroku-like PaaS experience on your own VPS.

### Setup

```bash
# 1. Install Dokploy on your VPS
curl -sSL https://dokploy.com/install.sh | sh

# 2. Access Dokploy dashboard at http://YOUR_VPS_IP:3000

# 3. Create a new project "qubot"
```

### Configuration in Dokploy UI

1. **Connect Git** — Add your repository URL
2. **Environment Variables** — Copy all variables from `.env.example`, fill values
3. **Services**:
   - `api`: build context `./backend`, port 8000, health check `/api/v1/system/health`
   - `worker`: build context `./backend`, command `python -m app.worker`
   - `frontend`: build context `./frontend`, port 3000
   - Add managed PostgreSQL and Redis databases
4. **Domains** — Configure your domain, enable SSL (Dokploy handles Let's Encrypt automatically)
5. **Deploy** — Click deploy; Dokploy builds and starts all services

### Post-Deploy Commands in Dokploy

Run via the Dokploy console (terminal panel in the UI):

```bash
# Run migrations
alembic upgrade head

# Seed data
python -m app.seeds.agent_classes
python -m app.seeds.admin_user
```

---

## 11. Health Monitoring

### `GET /api/v1/system/health` Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "services": {
    "postgres": {
      "status": "connected",
      "latency_ms": 2
    },
    "redis": {
      "status": "connected",
      "latency_ms": 0
    }
  },
  "version": "1.0.0"
}
```

### Implementation

```python
# backend/app/routers/system.py
from fastapi import APIRouter
from sqlalchemy import text
from app.database import get_session
from app.redis_client import get_redis
import time

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health")
async def health_check():
    results = {}

    # Check PostgreSQL
    try:
        start = time.monotonic()
        async with get_session() as session:
            await session.exec(text("SELECT 1"))
        results["postgres"] = {"status": "connected", "latency_ms": round((time.monotonic() - start) * 1000)}
    except Exception as e:
        results["postgres"] = {"status": "error", "error": str(e)}

    # Check Redis
    try:
        start = time.monotonic()
        redis = await get_redis()
        await redis.ping()
        results["redis"] = {"status": "connected", "latency_ms": round((time.monotonic() - start) * 1000)}
    except Exception as e:
        results["redis"] = {"status": "error", "error": str(e)}

    overall = "healthy" if all(s["status"] == "connected" for s in results.values()) else "degraded"

    return {
        "status": overall,
        "services": results,
        "version": "1.0.0"
    }
```

---

## 12. Security Hardening Checklist

```markdown
## Before Going Live

### Environment
- [ ] All passwords changed from defaults (POSTGRES_PASSWORD, JWT_SECRET_KEY)
- [ ] JWT_SECRET_KEY is at least 32 random characters
- [ ] .env is in .gitignore and never committed
- [ ] API keys loaded from env vars (never hardcoded in DB values)

### Network
- [ ] Postgres and Redis ports NOT exposed externally in prod (ports: [] in docker-compose.prod.yml)
- [ ] HTTPS enabled with valid certificate
- [ ] HTTP redirects to HTTPS
- [ ] CORS_ORIGINS set to exact production domain(s) only

### System
- [ ] UFW firewall: only ports 22, 80, 443 open
- [ ] SSH key-based auth only (disable password auth)
- [ ] Docker running as non-root inside containers (see Dockerfile USER directives)
- [ ] Automatic security updates enabled

### Application
- [ ] DEBUG=false in production
- [ ] LOG_LEVEL=INFO (not DEBUG) in production
- [ ] Health check endpoint accessible at /api/v1/system/health
```

---

## 13. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| API won't start | DB not ready | Check `docker compose ps postgres` — wait for healthy |
| `alembic upgrade head` fails | No DB connection | Verify POSTGRES_* vars in .env |
| WebSocket disconnects | Nginx timeout | Check `proxy_read_timeout 86400s` in nginx config |
| 502 Bad Gateway | Container not running | `docker compose logs api` — look for startup errors |
| Missing API keys | Env var not set | Add key to .env, `docker compose restart api` |
| `permission denied` on files | Volume mount owner | Check Dockerfile USER directive |
| Slow LLM responses | Model/provider issue | Check worker logs, verify api_key_ref points to correct env var |
| Tasks stuck in IN_PROGRESS | Worker crashed | `docker compose restart worker` |
