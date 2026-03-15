# Qubot Deployment Guide

Guía completa para desplegar Qubot localmente o en plataformas cloud como Dokploy.

## 🚀 Quick Start (Local)

### 1. Requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl (para health checks)

### 2. Clone y Configuración

```bash
# Clonar repositorio
git clone <your-repo-url>
cd Qubot

# Configurar variables de entorno (local)
cp .env.local .env

# O usar configuración de producción
cp .env.example .env
# Editar .env con tus valores
```

### 3. Deploy Local

```bash
# Opción 1: Script automatizado (recomendado)
./scripts/deploy-local.sh

# Opción 2: Comandos manuales
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verificar Deploy

```bash
# Verificar que todo funcione
./scripts/verify-deployment.sh

# O manualmente
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/info
```

## 📋 Comandos Útiles

```bash
# Deploy completo
./scripts/deploy-local.sh

# Ver logs
./scripts/deploy-local.sh logs

# Ver estado
./scripts/deploy-local.sh status

# Reiniciar
./scripts/deploy-local.sh restart

# Detener
./scripts/deploy-local.sh down

# Limpiar todo (incluye datos)
./scripts/deploy-local.sh clean
```

## 🌐 URLs Después del Deploy

| Servicio | URL |
|----------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Health | http://localhost:8000/api/v1/health |
| WebSocket | ws://localhost:8000/ws |

## 🔧 Configuración para Dokploy

### Variables de Entorno Requeridas

Ve a tu dashboard de Dokploy y configura estas variables:

```bash
# Core
DEBUG=false
SECRET_KEY=tu-clave-secreta-muy-larga-minimo-32-caracteres

# Database (Dokploy te dará estos valores)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis (Dokploy te dará estos valores)
REDIS_URL=redis://user:pass@host:6379/0

# LLM Providers (opcional pero recomendado)
OPENAI_API_KEY=sk-tu-openai-key
ANTHROPIC_API_KEY=sk-ant-tu-anthropic-key
GROQ_API_KEY=gsk-tu-groq-key

# Frontend
NEXT_PUBLIC_API_URL=https://tu-api-url/api/v1
NEXT_PUBLIC_WS_URL=wss://tu-api-url/ws
```

### Deploy en Dokploy

1. **Crear nuevo servicio** en Dokploy
2. **Conectar repositorio** Git
3. **Configurar build:**
   - Build Context: `./backend`
   - Dockerfile: `Dockerfile`
4. **Variables de entorno:** Agregar todas las del `.env.example`
5. **Puerto:** `8000`
6. **Health Check Path:** `/api/v1/health/ready`
7. **Deploy!**

### Deploy Frontend en Dokploy

1. **Crear nuevo servicio** (Static o Node)
2. **Build Command:** `npm install && npm run build`
3. **Publish Directory:** `out` (para Next.js static)
4. **Variables:**
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_WS_URL`

### Deploy Worker en Dokploy

1. **Crear nuevo servicio** tipo Worker
2. **Dockerfile:** `Dockerfile.worker`
3. **Mismas variables** que el API
4. **No expone puerto** (background worker)

## 🔐 Seguridad en Producción

### Antes de Deployar:

1. **Cambiar SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   ```

2. **Usar contraseñas seguras** para PostgreSQL

3. **Habilitar SSL/TLS** en Dokploy (automático)

4. **Configurar CORS correctamente:**
   ```bash
   ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com
   ```

5. **Rate Limiting:** Ya está habilitado por defecto

## 📊 Monitoreo

### Health Checks

Dokploy automáticamente usa estos endpoints:

- **Liveness:** `GET /api/v1/health/live`
- **Readiness:** `GET /api/v1/health/ready`
- **Metrics:** `GET /api/v1/metrics`

### Logs

```bash
# Local
docker-compose -f docker-compose.prod.yml logs -f api

# Dokploy
# Usar el dashboard de logs de Dokploy
```

## 🐛 Troubleshooting

### Problema: Puerto 8000 ya está en uso

```bash
# Cambiar puerto en .env
API_PORT=8001
```

### Problema: Base de datos no conecta

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs db

# Resetear base de datos (⚠️ borra datos)
./scripts/deploy-local.sh clean
./scripts/deploy-local.sh
```

### Problema: Redis no disponible

El sistema funciona sin Redis pero sin:
- Rate limiting distribuido
- WebSocket multi-instancia
- Worker queue

### Problema: LLM no responde

Verificar que las API keys estén configuradas:
```bash
# Probar OpenAI
curl http://localhost:8000/api/v1/llm-configs/{id}/test
```

## 🔄 Actualización

```bash
# Pull nuevos cambios
git pull origin main

# Rebuild y redeploy
./scripts/deploy-local.sh restart

# O en Dokploy: clic en "Redeploy"
```

## 💾 Backup y Restore

### Backup PostgreSQL

```bash
# Local
docker-compose -f docker-compose.prod.yml exec db pg_dump -U qubot qubot_db > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T db psql -U qubot qubot_db < backup.sql
```

### Backup Redis

```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE
```

## 🗑️ Cleanup

```bash
# Detener y eliminar contenedores
./scripts/deploy-local.sh down

# Eliminar todo incluyendo datos
./scripts/deploy-local.sh clean

# Eliminar imágenes también
docker system prune -a
```

## 📞 Soporte

Si tienes problemas:

1. Verificar logs: `./scripts/deploy-local.sh logs`
2. Verificar estado: `./scripts/deploy-local.sh status`
3. Health check: `./scripts/verify-deployment.sh`
4. Revisar variables: `cat .env`

## ✅ Checklist Pre-Deploy

- [ ] `.env` configurado con valores reales
- [ ] `SECRET_KEY` cambiado (no usar default)
- [ ] API keys de LLM agregadas (si se usan)
- [ ] CORS configurado con dominios reales
- [ ] SSL/TLS habilitado (Dokploy lo hace automático)
- [ ] Health checks funcionando
- [ ] Base de datos con backups configurados
- [ ] Logs monitoreables

## 🎉 Listo!

Tu aplicación debería estar corriendo en:
- **Local:** http://localhost:8000
- **Dokploy:** https://tu-app.dokploy.com
