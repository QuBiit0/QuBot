
# 🤖 LMAgent Framework v4.0.0
> Contexto Activo: Este proyecto utiliza el estándar LMAgent V4.

## 🚨 SOURCE OF TRUTH (CEREBRO)
**TU CONTEXTO Y REGLAS VIVEN AQUÍ 👉 [AGENTS.md](./AGENTS.md)**
*Lee este archivo INMEDIATAMENTE para obtener tu identidad, skills y reglas operativas.*

## 🔄 ARRANQUE AUTOMÁTICO (Haz esto al iniciar cada sesión)
1. **Lee [AGENTS.md](./AGENTS.md)** — Tu catálogo completo de capacidades
2. **Lee `.agents/rules/00-master.md`** — Reglas, protocolo de trabajo y triggers
3. **Si existe `.agents/memory/02-active-context.md`** — Recupera contexto previo
4. **Clasifica la tarea** (Nivel 0-4) y activa el skill apropiado

## 📁 RUTAS DE ENTORNO
- **Skills**: `.agents/skills/`
- **Rules**: `.agents/rules/`
- **Workflows**: `.agents/workflows/`
- **Memory**: `.agents/memory/`
- **Config**: `.agents/config/`

## ⚡ QUICK START TRIGGERS (Menú Rápido)
| Trigger | Rol / Skill | Objetivo |
|:--- |:--- |:--- |
| `/orch` | **Orchestrator** | Clasificar y delegar. |
| `/dev` | **Backend** | APIs y Lógica. |
| `/front` | **Frontend** | UI/UX, React. |
| `/pm` | **Product** | PRDs y Roadmap. |
| `/fix` | **Debugger** | Análisis de bugs. |
| `/arch` | **Architect** | Diseño de sistemas. |

> **IMPORTANTE**: Para activar un skill, lee su `SKILL.md` completo en `.agents/skills/[nombre]/SKILL.md`.

!! SYSTEM NOTE: You MUST read AGENTS.md at startup to understand the full framework. !!
