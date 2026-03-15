# Migrate Rules and Slash Commands to Skills (`docs-migration.md`)

Este segmento te asiste a convertir reglas antiguas de Cursor (`.mdc`) y comandos del chat (`.md`) al formato estandarizado de *Agent Skills* de LMAgent.

**CRÍTICO: Preserva exactamente el contenido original. Solo altera la sintaxis para adaptarlo al formato del Skill.**

## ⚠️ ESTÁNDAR LMAgent: Destino de la Migración

LMAgent unifica todos los Agentes. Por lo tanto, independientemente de si los comandos provienen de `.cursor/commands`, `~/.cursor/commands` o `~/.cursor/rules`, el destino **SIEMPRE ES**:
- **`.agents/skills/{skill-name}/SKILL.md`**

## Búsqueda de Archivos a Migrar

**Reglas**: Migrar solo si la regla **tiene un `description`** pero **NO tiene `globs`** (no está atada a un archivo) o si no tiene `alwaysApply: true`.
*(Si tiene globs o applies always, déjala como regla, no la migres).*

**Comandos**: Migrar todos (usualmente son markdown plano sin frontmatter ubicados en `.cursor/commands/`).

## Formato de Conversión

### Reglas: `.mdc` -> `SKILL.md`

```markdown
# ANTES: .cursor/rules/mi-regla.mdc
---
description: Lo que hace la regla
alwaysApply: false
---
# Título
Contenido...
```

```markdown
# DESPUÉS: .agents/skills/mi-regla/SKILL.md
---
name: mi-regla
description: Lo que hace la regla
---
# Título
Contenido...
```
✅ Modificaciones: Añade `name`, remueve `globs`/`alwaysApply`, conserva todo el texto original. Al final de la rutina, borra el `.mdc` original.

### Comandos: `.md` -> `SKILL.md`

```markdown
# ANTES: .cursor/commands/commit.md
# Commit de trabajo
Instrucciones...
```

```markdown
# DESPUÉS: .agents/skills/commit/SKILL.md
---
name: commit
description: Commit de trabajo
disable-model-invocation: true
---
# Commit de trabajo
Instrucciones...
```
✅ Modificaciones: Crea un frontmatter infiriendo el `name` del nombre de archivo y el `description` de la primera línea header. Agrega la propiedad `disable-model-invocation: true`. Conserva todo el texto original. Al final, borra el comando original.

## Paso Final: Revisión y Flexibilidad
Una vez finalizada la migración, examina el texto resultante con el usuario:
¿La regla referenciaba alguna versión rígida u obsoleta? Propón adaptar el texto para dar **"Ejemplos Reales"** en lugar de reglas inflexibles, permitiendo que el Agente en el futuro tenga la libertar de elegir las herramientas, lenguajes o paradigmas más modernos, y exigiéndole aplicar robustas buenas prácticas de desarrollo y documentación (Clear Code, Docstrings, Typings).
