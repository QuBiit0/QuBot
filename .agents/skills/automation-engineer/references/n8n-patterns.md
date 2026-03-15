# n8n & Make.com Patterns — Automation Engineer

> Patrones de integración y automatización para n8n y Make.com.

## Arquitectura de Workflows

### Patrón: Trigger → Process → Output

```
┌──────────┐   ┌──────────┐   ┌──────────┐
│ TRIGGER  │──▶│ PROCESS  │──▶│  OUTPUT  │
└──────────┘   └──────────┘   └──────────┘
  Webhook         Transform      Send Email
  Schedule        Validate       Update DB
  Event           Enrich         Call API
  Manual          Filter         Store File
```

### Patrón: Fan-Out / Fan-In

```
                ┌───▶ Service A ───┐
                │                  │
Trigger ──▶ Split ──▶ Service B ──▶ Merge ──▶ Output
                │                  │
                └───▶ Service C ───┘
```

## n8n: Patrones Comunes

### 1. Webhook → Validate → Process

```json
{
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "incoming-data",
        "authentication": "headerAuth"
      }
    },
    {
      "name": "Validate Input",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.email }}",
              "operation": "isNotEmpty"
            }
          ]
        }
      }
    }
  ]
}
```

### 2. Scheduled Sync

```
Schedule (every 1h) → Fetch from API → Transform → Upsert to DB → Notify on Error
```

### 3. Error Handling Pattern

```
Main Workflow → Try/Catch
                 ├── Success → Continue
                 └── Error → Log Error → Notify Slack → Retry Queue
```

## Variables de Entorno

> **REGLA:** Nunca hardcodear URLs, tokens o credenciales en workflows.

```
# .env para n8n
N8N_HOST=https://n8n.example.com
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change-me

# API Keys (usar credenciales de n8n, no env vars)
# Configurar en Settings > Credentials
```

## Checklist Pre-Deploy de Workflow

- [ ] Credenciales en el credential store, NO hardcodeadas
- [ ] Error handling en cada paso que puede fallar
- [ ] Logging suficiente para debugging
- [ ] Rate limiting respetado en APIs externas
- [ ] Timeout configurado en HTTP requests
- [ ] DLQ (Dead Letter Queue) para mensajes que fallan
- [ ] Alertas configuradas para failures
- [ ] Documentación del workflow (nombre, descripción, owner)
- [ ] Test con datos reales antes de activar producción

## Patrones de Retry

| Estrategia | Cuándo Usar |
|-----------|-------------|
| **Retry inmediato** (1x) | Errores transitorios (timeout) |
| **Retry con backoff** (3x, 1-5-25s) | APIs con rate limit |
| **DLQ** (sin retry automático) | Errores de datos/validación |
| **Circuit breaker** | API inestable |
| **Manual retry** | Errores que necesitan investigación |

## Seguridad en Automaciones

### ✅ Hacer:
- Usar webhook signatures para verificar origen
- Rotar API keys cada 90 días
- Limitar permisos de tokens al mínimo
- Usar OAuth2 en lugar de API keys cuando sea posible
- Encriptar datos en tránsito (HTTPS)

### ❌ NO Hacer:
- Exponer n8n sin autenticación
- Pasar tokens en query parameters
- Logear datos sensibles (passwords, tokens)
- Usar el mismo token para dev y producción
