# Módulo de Configuración de Qubot

## Resumen

El módulo de configuración de Qubot proporciona un sistema completo y flexible para gestionar todas las configuraciones del sistema. Soporta:

- **Variables de Entorno**: Configuración estática via `.env`
- **Base de Datos**: Configuración dinámica editable en tiempo real
- **API REST**: Endpoints completos para CRUD de configuraciones
- **Presets**: Guardar y aplicar configuraciones predefinidas
- **Historial**: Auditoría completa de cambios
- **Validación**: Validación automática de valores

## Estructura

```
app/
├── config.py                 # Variables de entorno (pydantic-settings)
├── models/
│   └── config.py            # Modelos SQLModel para DB
├── services/
│   └── config_service.py    # Lógica de negocio
└── api/endpoints/
    └── config.py            # Endpoints REST
```

## Tipos de Configuración

### 1. Variables de Entorno (Estáticas)

Archivo: `backend/app/config.py`

Configuraciones críticas del sistema que requieren reinicio:

```python
# Core
DEBUG, LOG_LEVEL, SECRET_KEY
DATABASE_URL, REDIS_URL

# LLM Providers (11 proveedores)
OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

# Messaging Bots
TELEGRAM_BOT_TOKEN, DISCORD_BOT_TOKEN, etc.

# Feature Flags
ENABLE_REGISTRATION, ENABLE_OLLAMA
```

### 2. Base de Datos (Dinámicas)

Tablas:
- `system_config`: Configuraciones editables
- `config_preset`: Plantillas de configuración
- `config_history`: Historial de cambios
- `environment_config`: Overrides por ambiente

## Categorías de Configuración

| Categoría | Descripción | Ejemplos |
|-----------|-------------|----------|
| `general` | Configuración general | app_name, maintenance_mode |
| `security` | Seguridad y autenticación | max_login_attempts, session_timeout |
| `llm` | Configuración de LLMs | llm_request_timeout, llm_enable_caching |
| `messaging` | Plataformas de mensajería | telegram_auto_setup |
| `features` | Feature flags | enable_user_registration, max_agents_per_user |
| `ui` | Interfaz de usuario | ui_theme, ui_language |
| `advanced` | Configuración avanzada | task_max_retries, cleanup_completed_tasks_days |

## API Endpoints

### CRUD Básico

```http
# Listar todas las configuraciones
GET /api/v1/config/

# Obtener una configuración específica
GET /api/v1/config/{key}

# Crear configuración
POST /api/v1/config/
{
  "key": "my_config",
  "value": "valor",
  "type": "string",
  "category": "general",
  "description": "Descripción"
}

# Actualizar configuración
PUT /api/v1/config/{key}
{
  "value": "nuevo_valor",
  "updated_by": "admin",
  "change_reason": "Razón del cambio"
}

# Eliminar configuración
DELETE /api/v1/config/{key}

# Actualización masiva
POST /api/v1/config/bulk-update
{
  "key1": "value1",
  "key2": "value2"
}
```

### Import/Export

```http
# Exportar configuración
GET /api/v1/config/export/all
GET /api/v1/config/export/all?category=security

# Importar configuración
POST /api/v1/config/import
{
  "config_key": {
    "value": "valor",
    "type": "string",
    "category": "general"
  }
}
```

### Presets

```http
# Listar presets
GET /api/v1/config/presets/list

# Crear preset
POST /api/v1/config/presets/create
{
  "name": "Production",
  "description": "Configuración para producción",
  "values": {"key1": "value1"},
  "category": "production"
}

# Aplicar preset
POST /api/v1/config/presets/{preset_id}/apply
```

### Historial

```http
# Ver historial de cambios
GET /api/v1/config/history/list
GET /api/v1/config/history/list?key=max_login_attempts&limit=50
```

### Categorías Específicas

```http
# Estado de LLM Providers
GET /api/v1/config/category/llm-providers

# Estado de Messaging
GET /api/v1/config/category/messaging

# Feature Flags
GET /api/v1/config/category/features

# Entorno actual
GET /api/v1/config/environment/current
```

### Inicialización

```http
# Inicializar configuraciones por defecto (ejecutar una vez)
POST /api/v1/config/initialize
```

## Uso desde el Código

### Usar ConfigService

```python
from app.services.config_service import ConfigService

async def my_function(session: AsyncSession):
    service = ConfigService(session)
    
    # Obtener valor
    max_attempts = await service.get_value("max_login_attempts", default=5)
    
    # Obtener con tipo
    timeout = await service.get_value_typed("session_timeout_hours", int, 24)
    
    # Actualizar
    await service.update("max_login_attempts", 10, updated_by="admin")
```

### Usar Variables de Entorno

```python
from app.config import settings

# Verificar si Telegram está configurado
if settings.telegram_enabled:
    token = settings.TELEGRAM_BOT_TOKEN

# Lista de orígenes permitidos
origins = settings.allowed_origins_list
```

## Configuraciones por Defecto

El sistema incluye **49 configuraciones por defecto** organizadas por categorías:

### General (4)
- `app_name`, `app_description`
- `maintenance_mode`, `maintenance_message`

### Security (6)
- `max_login_attempts`, `lockout_duration_minutes`
- `require_email_verification`, `session_timeout_hours`
- `password_min_length`, `password_require_special`

### LLM (8)
- `llm_request_timeout`, `llm_retry_attempts`
- `llm_enable_caching`, `llm_cache_ttl_minutes`
- `llm_cost_tracking_enabled`, `llm_fallback_enabled`
- `llm_max_tokens_limit`, `llm_streaming_enabled`

### Messaging (7)
- `telegram_auto_setup`, `telegram_allowed_users`
- `discord_auto_setup`, `discord_allowed_guilds`
- `slack_auto_setup`, `slack_allowed_workspaces`
- `whatsapp_auto_setup`, `messaging_rate_limit_per_minute`

### Features (8)
- `enable_user_registration`, `enable_public_agent_gallery`
- `enable_agent_sharing`, `enable_marketplace`
- `enable_analytics`, `enable_notifications`
- `max_agents_per_user`, `max_tasks_per_user_per_day`
- `enable_guest_mode`

### UI (7)
- `ui_theme`, `ui_language`, `ui_show_tour`
- `ui_items_per_page`, `ui_realtime_updates`
- `ui_agent_animations`, `ui_auto_save_interval`

### Advanced (6)
- `task_default_priority`, `task_max_retries`
- `task_retry_delay_seconds`, `worker_max_concurrent_tasks`
- `cleanup_completed_tasks_days`, `log_retention_days`

## Ejemplos de Uso

### Cambiar Configuración vía API

```bash
# Cambiar intentos de login máximos
curl -X PUT http://localhost:8000/api/v1/config/max_login_attempts \
  -H "Content-Type: application/json" \
  -d '{"value": 10, "updated_by": "admin", "change_reason": "Ajuste de seguridad"}'

# Habilitar modo mantenimiento
curl -X PUT http://localhost:8000/api/v1/config/maintenance_mode \
  -H "Content-Type: application/json" \
  -d '{"value": true}'

# Cambiar tema de UI
curl -X PUT http://localhost:8000/api/v1/config/ui_theme \
  -H "Content-Type: application/json" \
  -d '{"value": "light"}'
```

### Exportar/Importar Configuración

```bash
# Exportar
curl http://localhost:8000/api/v1/config/export/all > qubot-config-backup.json

# Importar
curl -X POST http://localhost:8000/api/v1/config/import \
  -H "Content-Type: application/json" \
  -d @qubot-config-backup.json
```

### Crear y Aplicar Preset

```bash
# Crear preset de producción
curl -X POST http://localhost:8000/api/v1/config/presets/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Producción",
    "description": "Configuración para ambiente productivo",
    "category": "production",
    "values": {
      "max_login_attempts": 3,
      "require_email_verification": true,
      "llm_cost_tracking_enabled": true,
      "enable_analytics": true
    }
  }'

# Aplicar preset
curl -X POST http://localhost:8000/api/v1/config/presets/{preset_id}/apply
```

## Variables de Entorno vs Base de Datos

| Aspecto | Variables de Entorno | Base de Datos |
|---------|---------------------|---------------|
| **Persistencia** | Archivo `.env` | PostgreSQL |
| **Reinicio** | Requiere reinicio | Aplica inmediatamente |
| **Seguridad** | No debe committearse | Encriptación opcional |
| **Auditoría** | No | Sí (historial completo) |
| **Escalabilidad** | Mismo para todos | Por tenant/organización |
| **Uso típico** | API keys, conexiones DB | Feature flags, límites |

## Buenas Prácticas

1. **Sensibles**: Guardar tokens y claves en variables de entorno
2. **Dinámicas**: Usar base de datos para flags y configuraciones UI
3. **Backup**: Exportar configuración regularmente
4. **Auditoría**: Revisar historial de cambios críticos
5. **Validación**: Siempre validar antes de aplicar cambios
6. **Documentación**: Documentar cambios en `change_reason`

## Seguridad

- Las configuraciones marcadas como `is_secret=True` se enmascaran en las respuestas API
- Los valores secretos deben almacenarse en variables de entorno
- El historial de cambios registra quién modificó qué y cuándo
- Las configuraciones no editables (`is_editable=False`) protegen valores críticos

## Troubleshooting

### Las configuraciones no se guardan
- Verificar conexión a base de datos
- Revisar logs: `docker-compose logs api`

### Configuración no aplica
- Verificar si `requires_restart=True`
- Revisar caché del navegador para configuraciones UI

### Errores de validación
- Usar endpoint `/api/v1/config/validate` para verificar antes de actualizar
- Revisar tipos de datos esperados (string, integer, boolean, json)
