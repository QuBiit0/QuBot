# 🧠 Prompt Engineering & Agent Communication

> **Tipo**: `rule` | **Versión**: 3.6.0 | **Archivos**: `11-prompt-engineering.md`

## 📌 Principios de Comunicación (Agent-to-Agent)

Cuando LMAgent delega tareas a sub-agentes (ej: `orchestrator` llama a `backend-engineer`), el prompt de handover **NUNCA** debe ser vago. La Inteligencia Artificial requiere contexto absoluto y *Zero Ambiguity*.

### 1. Instrucciones Estructuradas
Usa formatos predecibles (XML tags o Markdown Headers) para enmarcar las directivas, los constraints y los inputs.

```markdown
<context>
Estamos migrando de SQLite a PostgreSQL escalable en AWS.
</context>

<task>
Escribir el script de migración Alembic.
</task>

<constraints>
- Usar asyncpg como driver.
- Evitar locks de tabla enteros durante migraciones.
</constraints>
```

### 2. Few-Shot Prompting (Ejemplos Críticos)
Si esperas un formato específico de salida, no lo describas teóricamente, **muestra un ejemplo**.

> "Extrae los nombres en CSV. Formato esperado: `id, full_name, role`" -> `1, John Doe, ADMIN`

### 3. Delimitación contra Inyecciones
Cuando pases logs de consola, respuestas HTTP crudas, o input del usuario a al prompt, aíslalos mediante delimitadores robustos como triple comilla matemática o backticks para evitar que el LLM confunda los datos con instrucciones (Prompt Injection local).

### 4. System Prompts Dinámicos
Los System Prompts no deben ser estáticos de 10 páginas. Construye ensambladores que lean el `.agents/rules/` relevante y agreguen contexto progresivo dependiente de la tarea, optimizando así el *Context Window* y la precisión.
