# Creating Skills in Cursor (`docs-skills.md`)

Este anexo te guía para crear *Agent Skills* efectivos. Los Skills son archivos markdown que enseñan al agente cómo realizar tareas específicas en tu proyecto.

## ⚠️ ESTÁNDAR LMAgent: Destino de los Skills

**CRÍTICO**: A diferencia de la documentación original de Cursor que ubica los skills en `.cursor/skills/`, en este framework **TODOS LOS SKILLS se crean en el directorio universal `.agents/skills/`**. Esto garantiza que los skills que crees sean compatibles con los **37 agentes** soportados por LMAgent (Cursor, Claude Code, Windsurf, Copilot, etc.).

## Estructura del Archivo Skill

Los skills son directorios que contienen un archivo `SKILL.md` principal:

```
.agents/skills/nombre-del-skill/
├── SKILL.md              # Requerido - Instrucciones principales
├── reference.md          # Opcional - Documentación detallada
└── examples.md           # Opcional - Ejemplos de uso
```

### Estructura del `SKILL.md`

Todo skill requiere un archivo `SKILL.md` con YAML frontmatter y cuerpo Markdown:

```markdown
---
name: tu-nombre-de-skill
description: Descripción breve de lo que hace el skill y cuándo usarlo (¡CLAVE!)
---

# Título del Skill

## Instrucciones
...
```

| Campo | Requisitos |
|-------|--------------|
| `name` | Máx. 64 caracteres, letras minúsculas y guiones. |
| `description` | Especifica **QUÉ** hace y **CUÁNDO** debe usarse el skill. Describe al agente en tercera persona (ej. *"Evalúa pull requests. Úsalo cuando el usuario pida revisar código."*). |

## Mejores Prácticas de Creación

1. **Escribir Descripciones Efectivas (Triggers)**
   El campo `description` del frontmatter se inyecta en el system prompt. Es como el "Trigger" del agente.
   - ✅ **Bien**: "Extrae texto y tablas de archivos PDF. Úsalo al trabajar con PDFs o si el usuario pide extracción."
   - ❌ **Mal**: "Ayuda con documentos."

2. **Progressive Disclosure (Revelación Progresiva)**
   Mantén el `SKILL.md` **corto** (idealmente menos de 50 a 100 líneas). Si necesitas darle al agente largas cantidades de contexto, refiérelo a archivos anexos (`[Ver referencia](reference.md)`) para que el agente los lea solo cuando sea necesario. Esto maximiza la eficiencia de tokens.

3. **Flexibilidad Universal de Herramientas (Estándar LMAgent)**
   - NUNCA obligues al skill a usar una librería anticuada. Proporciona las dependencias como "Ejemplos de referencia" e indica al agente que es libre de sugerir herramientas modernas u óptimas.
   - ❌ **Mal**: "Usa Python 3.9 y Pandas 1.0."
   - ✅ **Bien**: "Ejemplo usando Python 3.11+ y Pandas. Valida si la librería es adecuada para los requerimientos actuales."

4. **Buenas Prácticas de Desarrollo y Documentación**
   - Asegúrate que las instrucciones del skill requieran que el agente documente su código (ej. TSDoc o Docstrings).
   - Inculca el desarrollo modular (Clean Code o componentes separados) como principio dentro del skill.
