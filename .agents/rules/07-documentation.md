# Documentación Continua

> **Tipo**: `rule` | **Versión**: 3.0.0 | **Actualización**: 2026-02

## 📌 Quick Reference

| ¿Qué documentar? | ¿Dónde? |
|------------------|--------|
| Decisiones de stack | `02-tech-stack.md` |
| Patrones de código | `03-code-style.md` |
| Flujos de trabajo | `01-workflow.md` |
| Comandos del proyecto | `config/commands.yaml` |
| Cambios de versión | `CHANGELOG.md` |

### Regla de Oro
> "⚡ Si pensaste más de 5 minutos en algo, probablemente vale la pena documentarlo."

### 👥 Roles que usan esta regla
`technical-writer`, `backend-engineer`, `frontend-engineer`, `architect`

---

> ⚠️ **FLEXIBILIDAD DE FORMATOS**: Los nombres de archivo y estructuras mencionadas (ej. `CHANGELOG.md`) son **ejemplos convencionales**. Eres libre de adaptar y proponer las herramientas y formatos de documentación que mejor se alineen con los estándares más actuales de la industria.

> ⚠️ **REGLA CRÍTICA**: Esta regla debe aplicarse SIEMPRE, en cada sesión de trabajo.

## Cuándo Documentar

### Después de CADA implementación significativa:

1. **Nuevas funcionalidades** → Actualizar README o docs relevantes
2. **Cambios de arquitectura** → Actualizar `02-tech-stack.md` o crear diagrama
3. **Nuevos patrones** → Documentar en reglas aplicables
4. **Bugs resueltos** → Agregar a CHANGELOG o notas
5. **Decisiones técnicas** → Documentar el "por qué"

### Al usar el framework:

1. **Nuevas reglas aprendidas** → Agregar a `rules/`
2. **Workflows útiles** → Crear en `workflows/`
3. **Comandos frecuentes** → Agregar a `config/commands.yaml`
4. **Personas personalizadas** → Crear en `personas/`

## Qué Documentar

| Tipo | Dónde | Ejemplo |
|------|-------|---------|
| Decisiones de stack | `02-tech-stack.md` | "Usamos PostgreSQL porque..." |
| Patrones de código | `03-code-style.md` | "Nombres de funciones en snake_case" |
| Flujos de trabajo | `01-workflow.md` | "PRs requieren 2 reviewers" |
| Comandos del proyecto | `config/commands.yaml` | Alias personalizados |
| Changelog | `CHANGELOG.md` | Versiones y cambios |

## Instrucciones para el Agente

> **SIEMPRE al finalizar una tarea**:

```markdown
## Checklist de Cierre

- [ ] ¿Creé algo nuevo que otros deberían saber?
- [ ] ¿Cambié algún patrón o convención?
- [ ] ¿Resolví un problema que podría repetirse?
- [ ] ¿Las reglas actuales siguen siendo válidas?

Si respondí SÍ a cualquiera → ACTUALIZAR DOCUMENTACIÓN
```

## Formato Recomendado

### Para reglas nuevas:

```markdown
## [Nombre de la Regla]

**Contexto**: Por qué existe esta regla
**Regla**: Qué hacer específicamente
**Ejemplo**: Código o configuración de ejemplo
**Excepciones**: Cuándo no aplica (si hay)
```

### Para cambios:

```markdown
## [Fecha] - [Título del Cambio]

**Antes**: Cómo era
**Después**: Cómo es ahora
**Razón**: Por qué se cambió
```

## Recordatorio Automático

Si el agente no documenta cambios significativos, recordarle:

> "¿No deberías documentar este cambio en [archivo relevante]?"

---

**⚡ Regla de oro**: Si tuviste que pensar más de 5 minutos en algo, probablemente vale la pena documentarlo.
