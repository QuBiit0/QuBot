# ⚡ Automation & Workflows Rules
> **Tipo**: `rule` | **Versión**: 3.0.0 | **Referencia**: `automation-engineer`

## 📌 Scope
Reglas para automatizaciones con **n8n**, **Zapier**, **GitHub Actions**, y **Webhooks**.

> ⚠️ **FLEXIBILIDAD DE PLATAFORMAS**: Las plataformas mencionadas (ej. `n8n`, `Zapier`) son **ejemplos de referencia**. Tienes libertad para evaluar y proponer herramientas modernas de orquestación o automatización que mejor encajen con los requerimientos técnicos del proyecto.

## 🛡️ Security
1. **Secretos**: NUNCA hardcodear API Keys. Usar `ENV_VARS` o Vaults.
2. **Webhooks**: Validar firmas (HMAC) siempre que sea posible.
3. **Rate Limits**: Implementar backoff exponencial para retries.

## 🏗️ n8n Standards
- **Nodos**: Nombrar nodos descriptivamente (ej: `Get User Data` vs `HTTP Request`).
- **Error Trigger**: Todo workflow crítico debe tener un "Error Trigger" que notifique a Slack/Discord.
- **Idempotencia**: Los workflows deben poder re-ejecutarse sin duplicar efectos (ej: `upsert` en lugar de `insert`).

## 📝 Documentation
- Cada workflow debe tener una nota de "Descripción" en el canvas.
- Exportar JSON del workflow al repositorio en `.agents/workflows/n8n/`.
