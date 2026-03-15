# Creating Custom Subagents (`docs-subagents.md`)

Este anexo te guía para crear subagentes personalizados en Cursor. Un subagente es un asistente especializado que corre en contextos aislados con un "system prompt" a medida.

## Cuándo usar Subagentes

- **Preservar contexto** aislando exploraciones de la conversación principal.
- **Especializar comportamiento** con prompts altamente enfocados.
- **Reusar configuraciones**.

## Ubicaciones
| Ubicación | Alcance | Prioridad |
|----------|-------|----------|
| `.cursor/agents/` | Proyecto actual | Mayor |
| `~/.cursor/agents/` | Todos tus proyectos | Menor |

## Formato del Archivo Subagente

Crea un archivo `.md` con YAML frontmatter y un cuerpo markdown (este será el system prompt):

```markdown
---
name: code-reviewer
description: Especialista experto en code review. Revisa proactivamente código en busca de calidad, seguridad y mantenibilidad. Usar inmediatamente tras modificar código.
---

Eres un revisor de código senior garantizando altos estándares.
Al ser invocado:
1. Revisa el git diff para ver cambios recientes.
2. Comienza la revisión basándote en estándares de la industria.
[...Resto del prompt...]
```

### Campos Requeridos
- `name`: Identificador único (letras minúsculas y guiones).
- `description`: Cuándo delegar a este agente. **DEBE SER ESPECÍFICO.** Incluye "use proactively" o "usa proactivamente". Por ejemplo: *"Especialista en depuración. Úsalo proactivamente al encontrar errores de CI/CD."*

## Mejores Prácticas

1. **Diseñar subagentes enfocados**: Cada uno debe sobresalir en *una* tarea.
2. **Descripciones detalladas**: Incluye términos disparadores (triggers) para que la IA sepa cuándo delegar.
3. **Flexibilidad de Versiones (ESTÁNDAR LMAgent)**: Evita atar el system prompt del subagente a una herramienta o versión anticuada. Pide que el subagente utilice "las mejores prácticas y librerías disponibles a la fecha".
