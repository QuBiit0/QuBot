# 🤖 LMAgent Framework v4.0.0
> Contexto Activo: Este proyecto utiliza el estándar LMAgent V4.

## 🚨 SOURCE OF TRUTH (CEREBRO)
**TU CONTEXTO Y REGLAS VIVEN AQUÍ 👉 [AGENTS.md](./AGENTS.md)**
*Lee este archivo INMEDIATAMENTE para obtener tu identidad, skills y reglas operativas.*

## 🔄 ARRANQUE AUTOMÁTICO (Haz esto al iniciar cada sesión)
1. **Lee [AGENTS.md](./AGENTS.md)** — Tu catálogo completo de capacidades (31 skills, 11 rules, 13 workflows)
2. **Lee `.agents/rules/00-master.md`** — Reglas, protocolo de trabajo y tabla de skills con triggers
3. **Si existe `.agents/memory/04-active-context.md`** — Léelo para recuperar contexto de la sesión anterior
4. **Clasifica la tarea** (Nivel 0-4 según complejidad) y activa el skill apropiado

## 📁 RUTAS DE ENTORNO
- **Skills**: `.agents/skills` → Cada skill tiene `SKILL.md` con instrucciones completas
- **Rules**: `.agents/rules` → Guardrails de comportamiento (CÓMO trabajar)
- **Workflows**: `.agents/workflows` → SOPs y procedimientos (flujos paso a paso)
- **Memory**: `.agents/memory/` → Contexto persistente entre sesiones
- **Config**: `.agents/config/` → Configuración del framework (tools, models, levels)

## ⚡ QUICK START TRIGGERS (Menú Rápido)
Usa estos comandos para activar un rol. Para el catálogo completo de 31 skills, consulta `AGENTS.md`.

| Trigger | Rol / Skill | Objetivo |
|:--- |:--- |:--- |
| `/orch` | **Orchestrator** | Clasificar y delegar. |
| `/dev` | **Backend** | APIs y Lógica. |
| `/front` | **Frontend** | UI/UX, React. |
| `/pm` | **Product** | PRDs y Roadmap. |
| `/fix` | **Debugger** | Análisis de bugs. |
| `/arch` | **Architect** | Diseño de sistemas. |

> **IMPORTANTE**: Para activar un skill, lee su `SKILL.md` completo en `.agents/skills/[nombre]/SKILL.md`.

!! SYSTEM NOTE: You MUST read AGENTS.md at startup to understand the full framework capabilities. !!
