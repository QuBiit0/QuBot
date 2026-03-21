# Contexto Activo - Qubot

## Fecha: 2026-03-20 (Evening)

## Estado del Proyecto: ✅ Funcional

### Containers
- qubot-api: ✅ Running (healthy)
- qubot-db: ✅ Running (healthy)
- qubot-frontend: ✅ Running (healthy)
- qubot-worker: ✅ Running (healthy)
- qubot-redis: ✅ Running (healthy)
- qubot-nginx: ✅ Running

### Credenciales
- **Admin**: `admin@qubot.ai` / `admin`
- **DB**: `qubot:qubot_pass@db:5432/qubot_db`

---

## Último Trabajo Completado

### Fixes aplicados:
1. ✅ Chat pages mejorados (/chat y /webchat)
   - Botón "Office" añadido
   - Indicador de conexión WiFi
   - Mensajes de error amigables
   - Health check automático cada 30s

2. ✅ Servicio layer añadido
   - docker_sandbox_service
   - loop_detection_service
   - script_execution_service
   - tool_profile_service

3. ✅ Integrations module
   - Calendar (Google, Outlook)
   - Voice (OpenAI)

4. ✅ Skills system
   - 5 skills definidos en backend/app/skills/

5. ✅ Fix de credenciales DB
   - DB password sincronizada con docker-compose.yml

---

## Commits Recientes (今晚)

```
[master 5e7044b] docs: update changelog for v1.1.0
[master 38f494b] fix(docker): update database credentials to match .env
[master 0e9eb08] feat(frontend): update UI components and pages
[master ebd4e9a] feat(backend): add service layer and integrations
[master 54b2d34] feat(frontend): add home button and friendly error messages to chat pages
```

---

## Para Continuar Mañana

### Issues pendientes:
1. **WebChat API** - Necesita testing real con el endpoint `/chat/stream`
2. **Skills marketplace** - UI existe, necesita conectar con backend
3. **Voice integration** - UI existe, necesita testing
4. **Calendar integration** - UI existe, necesita testing
5. **SecretsManager UI** - Página existe, necesita testing completo

### Testing recomendado:
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@qubot.ai","password":"admin"}'

# Test chat stream
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"message":"Hello"}'
```

---

## Links Útiles
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Nginx: http://localhost:80
